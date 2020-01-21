# to get rid of alsa sound errors: see https://raspberrypi.stackexchange.com/questions/83254/pygame-and-alsa-lib-error
import os

from shapely.geometry import Polygon

from gameengine.gameactors import Actor, Paddle, Ball, Net, BallFlavor

os.environ['SDL_AUDIODRIVER'] = 'dsp'

from collections import namedtuple
from threading import RLock
from typing import Dict, Optional, List, Tuple

import pygame
from pygame import font

from config import logging_configurator
from config.property_configurator import game_render_config
from gameengine.arena import Arena
from gameengine.collision_engine import GameCollisionEngine
from gamerender.scorecards import StandardScoreCard
from proto_gen.gamemaster_pb2 import PlayerIdentifier, PaddleType

logger = logging_configurator.get_logger(__name__)
color_config = game_render_config.color_config

# a puzzling requirement for 'initializing' all the pygame modules.
# apparently, if performance is an issue, you just initialize the modules you need, but not a problem right now
pygame.init()

SCORE_BOARD_HEIGHT = 150
META_DATA_HEIGHT = 50
REGISTRATION_OFFSET_HORIZ = 10
SEPARATOR = 5

registration_lock = RLock()
game_lock = RLock()
pygame.display.set_caption("Pong is only for the brave")

# surface is expected to be a pygame surface and pos is (x,y) of where surface is to be rendered on the canvas
GamePane = namedtuple("GamePane", ['surface', 'pos'])

# player_id is expected to be PlayerIdentifer object and scorecard a StandardScoreCard
RegisteredPlayer = namedtuple("RegisteredPlayer", ['player_id', 'scorecard'])

def color_from_ball(actor: Ball) -> Tuple[int,int,int]:
    if actor.flavor is BallFlavor.PRIMARY:
        color = color_config.primary_ball_color
    elif actor.flavor is BallFlavor.GROW_PADDLE:
        color = color_config.grow_paddle_ball_color
    elif actor.flavor is BallFlavor.SHRINK_PADDLE:
        color = color_config.shrink_paddle_ball_color
    else:
        color = (0, 0, 0)
    return color


def color_from_actor(actor: Actor) -> Tuple[int,int,int]:
    if isinstance(actor, Paddle):
        color = color_config.paddle_color
    elif isinstance(actor, Ball):
        color = color_from_ball(actor)
    elif isinstance(actor, Net):
        color = color_config.net_color
    else:
        color = color_config.obstacle_color
    return color

class CachedScoreFontImages:
    def __init__(self, scorecard: StandardScoreCard):
        self.fontconfig = game_render_config.score_board_font
        self.font = pygame.font.SysFont(self.fontconfig.name,
                                        self.fontconfig.size,
                                        self.fontconfig.is_bold,
                                        self.fontconfig.is_italic)
        self._player_name: Optional[str] = None
        self._paddle_strategy_name: Optional[str] = None
        self._match_points: Optional[int] = None
        self._total_points: Optional[int] = None
        self._matches_won: Optional[int] = None
        self.name_image: Optional[pygame.Surface] = None
        self.paddle_stategy_image: Optional[pygame.Surface] = None
        self.match_points_image: Optional[pygame.Surface] = None
        self.total_points_image: Optional[pygame.Surface] = None
        self.matches_won_image: Optional[pygame.Surface] = None
        self.update(scorecard)

    def ordered_images(self) -> List[pygame.Surface]:
        return [self.name_image, self.paddle_stategy_image, self.match_points_image, self.total_points_image,
                self.matches_won_image]

    @property
    def is_updated(self):
        return self._image_updated

    @property
    def player_name(self) -> str:
        return self._player_name

    @player_name.setter
    def player_name(self, name: str):
        if name != self._player_name:
            self._player_name = name
            self._update_name_image()
            self._image_updated = True

    @property
    def paddle_strategy_name(self) -> str:
        return self._paddle_strategy_name

    @paddle_strategy_name.setter
    def paddle_strategy_name(self, name):
        if name != self._paddle_strategy_name:
            self._paddle_strategy_name = name
            self._update_strategy_image()
            self._image_updated = True

    @property
    def match_points(self) -> int:
        return self._match_points

    @match_points.setter
    def match_points(self, points: int):
        if points != self._match_points:
            self._match_points = points
            self._update_match_points_image()
            self._image_updated = True

    @property
    def total_points(self) -> int:
        return self._total_points

    @total_points.setter
    def total_points(self, points: int):
        if points != self._total_points:
            self._total_points = points
            self._update_total_points_image()
            self._image_updated = True

    @property
    def matches_won(self) -> int:
        return self._matches_won

    @matches_won.setter
    def matches_won(self, count: int):
        if count != self._matches_won:
            self._matches_won = count
            self._update_matches_won_image()
            self._image_updated = True

    def update(self, scorecard: StandardScoreCard):
        self.image_updated = False
        self.player_name = scorecard.player_identifier.player_name
        self.paddle_strategy_name = scorecard.player_identifier.paddle_strategy_name
        self.match_points = scorecard.current_match_points_won
        self.total_points = scorecard.total_points_won
        self.matches_won = scorecard.matches_won

    def _update_name_image(self):
        self.name_image = self.font.render(f"Player Name: {self.player_name}", True, self.fontconfig.color)

    def _update_strategy_image(self):
        self.paddle_stategy_image = self.font.render(f"Paddle Strategy: {self.paddle_strategy_name}", True, self.fontconfig.color)

    def _update_match_points_image(self):
        self.match_points_image = self.font.render(f"Match Points: {self.match_points}", True, self.fontconfig.color)

    def _update_total_points_image(self):
        self.total_points_image = self.font.render(f"Total Points: {self.total_points}", True,  self.fontconfig.color)

    def _update_matches_won_image(self):
        self.matches_won_image = self.font.render(f"Match Count: {self.matches_won}", True,  self.fontconfig.color)


class DefaultPongRenderer:
    def __init__(self, arena: Arena, game_engine: GameCollisionEngine):
        self.arena = arena
        self.game_engine = game_engine

        self.scoreboard_font_info = game_render_config.score_board_font
        self.registration_font_info = game_render_config.registration_font
        self.commencement_font_info = game_render_config.commencement_font

        self.scoreboard_font = pygame.font.SysFont(self.scoreboard_font_info.name,
                                                   self.scoreboard_font_info.size,
                                                   self.scoreboard_font_info.is_bold,
                                                   self.scoreboard_font_info.is_italic)

        self.registration_font = pygame.font.SysFont(self.registration_font_info.name,
                                                     self.registration_font_info.size,
                                                     self.registration_font_info.is_bold,
                                                     self.registration_font_info.is_italic)

        self.commencement_font = pygame.font.SysFont(self.commencement_font_info.name,
                                                     self.commencement_font_info.size,
                                                     self.commencement_font_info.is_bold,
                                                     self.commencement_font_info.is_italic)

        # the game canvas from top to bottom comprises three 'panes' stretched fully across canvas width:
        # Scoreboard surface + buffer
        # Meta Data surface + buffer
        # Areana surface + buffer
        self.canvas_width = self.arena.arena_width
        self.canvas_height = SCORE_BOARD_HEIGHT + SEPARATOR + META_DATA_HEIGHT + SEPARATOR + self.arena.arena_height + SEPARATOR
        self.canvas = pygame.display.set_mode([self.canvas_width, self.canvas_height])

        # create the scoreboard surface, meta-data surface, and arena surface and record their positions on the canvas
        score_y_pos = 0
        metadata_y_pos = score_y_pos + SCORE_BOARD_HEIGHT + SEPARATOR
        arena_y_pos = metadata_y_pos + META_DATA_HEIGHT + SEPARATOR
        self.scoreboard_pane = GamePane(pygame.Surface((self.arena.arena_width, SCORE_BOARD_HEIGHT)), (0, score_y_pos))
        self.metadata_pane = GamePane(pygame.Surface((self.arena.arena_width, META_DATA_HEIGHT)), (0, metadata_y_pos))
        self.arena_pane = GamePane(pygame.Surface((self.arena.arena_width, self.arena.arena_height)), (0, arena_y_pos))

        # dict to track registerd players.  key is paddle type and value is registered player
        self.registered_player_by_paddle_type: Dict[PaddleType, RegisteredPlayer] = {}
        self.cached_score_fonts_by_paddle_type: Dict[PaddleType, CachedScoreFontImages] = {}

        # specify positions for the registration notifications
        self.player_left_registration_pos = (REGISTRATION_OFFSET_HORIZ, 0)
        self.player_right_registration_pos = (REGISTRATION_OFFSET_HORIZ, self.registration_font_info.size + SEPARATOR)

        # specify position for game commencement notification
        self.commencement_pos = (0, self.canvas_height // 2)

        self.game_started: bool = False
        self.registration_closed: bool = False

    def register_player(self, player: PlayerIdentifier):
        with registration_lock:
            if self.game_started:
                logger.warn("Game has already started.  Not taking new registrations")
                return

            if self.registration_closed:
                logger.warn("Maximum number of players already registered")
                return

            if player.paddle_type in self.registered_player_by_paddle_type:
                logger.warn(
                    f"Cannot register player {player.player_name}-{player.paddle_strategy_name} because {player.paddle_type} already registered")
                return

            scorecard = StandardScoreCard(player)
            self.registered_player_by_paddle_type[player.paddle_type] = RegisteredPlayer(player, scorecard)
            self.cached_score_fonts_by_paddle_type[player.paddle_type] = CachedScoreFontImages(scorecard)

            for paddle_type, registered_player in self.registered_player_by_paddle_type.items():
                player_info_str = ":".join(
                    (registered_player.player_id.player_name, registered_player.player_id.paddle_strategy_name))
                registration_image = self.registration_font.render(f"Player {player_info_str} has registered",
                                                                   True, self.registration_font_info.color)
                font_pos = self.player_left_registration_pos if paddle_type is PaddleType.LEFT else self.player_right_registration_pos
                self.canvas.blit(registration_image, font_pos)
            self.registration_closed = len(self.registered_player_by_paddle_type) == 2
            pygame.display.update()

    def draw_arena(self, screen):
        pass
        # black = (0, 0, 0)
        # white = (255, 255, 255)
        # screen.fill(black)
        # pygame.draw.rect(screen, white, ((0, 0), (self.screen_width, self.screen_height)), 20)

    def render_commencement(self):
        blit_rectangle = None
        for countdown in reversed(range(4)):
            pygame.time.delay(1000)
            commencement_image = self.commencement_font.render(f"Pong Experience Beginning in ... {countdown}",
                                                              True, self.commencement_font_info.color)
            if blit_rectangle:
                self.canvas.fill((0,0,0), blit_rectangle)
            blit_rectangle = self.canvas.blit(commencement_image, self.commencement_pos)
            pygame.display.update()

    def update_panes(self) -> List[pygame.Rect]:
        """
        This wil blit score changes to the working canvas.
        :return: A list of rectangles that can be used for pygame.display.update that represent
        canvas areas that were updated
        """
        blitted_rectangles = []
        blitted_rectangles.extend(self.update_score_pane())
        blitted_rectangles.extend(self.update_meta_pane())
        blitted_rectangles.extend(self.update_arena_pane())
        return blitted_rectangles

    def update_score_pane(self) -> List[pygame.Rect]:
        """
        This wil blit score changes to the working canvas.
        :return: A list of rectangles that can be used for pygame.display.update that represent
        canvas areas that were updated
        """
        surface = self.scoreboard_pane.surface
        left_score_fonts = self.cached_score_fonts_by_paddle_type[PaddleType.LEFT]
        right_score_fonts = self.cached_score_fonts_by_paddle_type[PaddleType.RIGHT]
        if not left_score_fonts.is_updated or not right_score_fonts.is_updated:
            return []

        # wipe out what was there before
        surface.fill(color_config.score_color)
        spacer = self.scoreboard_font_info.size + SEPARATOR

        # populate left hand side
        x_start = 0
        y_start = SEPARATOR
        for font_image in left_score_fonts.ordered_images():
            surface.blit(font_image, (x_start, y_start))
            y_start += spacer

        # populate right hand side
        x_start = self.canvas_width // 2 + SEPARATOR
        y_start = SEPARATOR
        for font_image in right_score_fonts.ordered_images():
            surface.blit(font_image, (x_start, y_start))
            y_start += spacer
        return [self.canvas.blit(surface, self.scoreboard_pane.pos)]

    def update_meta_pane(self) -> List[pygame.Rect]:
        """
        This wil blit score changes to the working canvas.
        :return: A list of rectangles that can be used for pygame.display.update that represent
        canvas areas that were updated
        """
        surface = self.metadata_pane.surface
        surface.fill(color_config.meta_color)
        return [self.canvas.blit(surface, self.metadata_pane.pos)]

    def update_arena_pane(self) -> List[pygame.Rect]:
        """
        This wil blit score changes to the working canvas.
        :return: A list of rectangles that can be used for pygame.display.update that represent
        canvas areas that were updated
        """
        surface = self.arena_pane.surface
        surface.fill(color_config.arena_color)
        for actor in self.arena.actors:
            color = color_from_actor(actor)
            shape: Polygon = actor.shape
            coords = list(shape.exterior.coords)
            pygame.draw.polygon(surface, color, coords)
        return [self.canvas.blit(surface, self.arena_pane.pos)]

    def start_game(self):
        with game_lock:
            if not self.registration_closed:
                logger.warn("Game cannot start until all players are registered")
                return

            if self.game_started:
                logger.warn("Game is already started!")
                return
            self.game_started = True

        self.render_commencement()
        pygame.display.update(self.update_panes())


        # fps_clock = pygame.time.Clock()
        #
        # while True:
        #     for event in pygame.event.get():
        #         if event.type == pygame.QUIT:
        #             pygame.quit()
        #             sys.exit()
        #
        #     self.draw_arena(screen)
        #
        #     fps = self.fps_font.render(str(int(fps_clock.get_fps())), True, pygame.Color('white'))
        #     self.canvas.blit(fps, (50, 50))
        #     pygame.display.update()
        #
        #     screen_array = surfarray.array3d(screen)
        #
        #     fps_clock.tick(24)
