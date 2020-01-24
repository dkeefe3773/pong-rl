# to get rid of alsa sound errors: see https://raspberrypi.stackexchange.com/questions/83254/pygame-and-alsa-lib-error
import os
import sys
from queue import Queue, Empty

from pygame.time import Clock
from shapely.geometry import Polygon

from gameengine.gameactors import Actor, Paddle, Ball, Net, BallFlavor, BackLine
from gamerender.caches import CachedScoreFontImages
from translators.proto_translations import GameStateBuilder

os.environ['SDL_AUDIODRIVER'] = 'dsp'

from collections import namedtuple
from threading import RLock
from typing import Dict, List, Tuple, Optional

import pygame
from pygame import font

from config import logging_configurator
from config.property_configurator import game_render_config
from config.property_configurator import game_engine_config
from config.property_configurator import server_client_communication_config
from gameengine.arena import Arena
from gameengine.collision_engine import GameCollisionEngine
from gamerender.scorecards import ScoreKeeper
from proto_gen.gamemaster_pb2 import PlayerIdentifier, PaddleType, PaddleAction, PaddleDirective

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
pygame.display.set_caption("Pong!")

# surface is expected to be a pygame surface and pos is (x,y) of where surface is to be rendered on the canvas
GamePane = namedtuple("GamePane", ['surface', 'pos'])

# player_id is expected to be PlayerIdentifer object and scorecard a StandardScoreCard
RegisteredPlayer = namedtuple("RegisteredPlayer", ['player_id'])

# game is capped at this fps
FPS_CAP = game_render_config.fps_cap

# the blocking timeout for the queue
ACTION_QUEUE_TIMEOUT = server_client_communication_config.action_queue_timeout

# the speed of the paddle in the y direction
DEFAULT_PADDLE_SPEED = game_engine_config.default_paddle_speed


def color_from_ball(actor: Ball) -> Tuple[int, int, int]:
    if actor.flavor is BallFlavor.PRIMARY:
        color = color_config.primary_ball_color
    elif actor.flavor is BallFlavor.GROW_PADDLE:
        color = color_config.grow_paddle_ball_color
    elif actor.flavor is BallFlavor.SHRINK_PADDLE:
        color = color_config.shrink_paddle_ball_color
    else:
        color = (0, 0, 0)
    return color


def color_from_actor(actor: Actor) -> Tuple[int, int, int]:
    if isinstance(actor, Paddle):
        color = color_config.paddle_color
    elif isinstance(actor, Ball):
        color = color_from_ball(actor)
    elif isinstance(actor, Net):
        color = color_config.net_color
    elif isinstance(actor, BackLine):
        color = color_config.backline_color
    else:
        color = color_config.obstacle_color
    return color


paddle_directive_to_velocity = {
    PaddleDirective.UP: (0, -DEFAULT_PADDLE_SPEED),
    PaddleDirective.DOWN: (0, DEFAULT_PADDLE_SPEED),
    PaddleDirective.STATIONARY: (0, 0)
    }


def get_paddle_velocity(paddle_directive: PaddleDirective) -> Tuple[int, int]:
    """
    :param paddle_directive:  a directive for paddle direction
    :return:  the velocity as 2-tuple
    """
    return paddle_directive_to_velocity.get(paddle_directive, (0, 0))


class DefaultPongRenderer:
    def __init__(self, arena: Arena, game_engine: GameCollisionEngine,
                 left_paddle_queue: Queue, right_paddle_queue: Queue,
                 left_game_state_queue: Queue, right_game_state_queue):
        """

        :param arena:                This contains all the actors
        :param game_engine:          Provices the collision physics
        :param left_paddle_queue:    Thread safe queue for incoming left paddle actions
        :param right_paddle_queue:   Thread safe queue for incoming right paddle actions
        :param left_game_state_queue:     Thread safe queue for outgoing game state to left paddle player
        :param right_game_state_queue:     Thread safe queue for outgoing game state to right paddle player
        """
        self.arena = arena
        self.game_engine = game_engine
        self.left_paddle_queue = left_paddle_queue
        self.right_paddle_queue = right_paddle_queue
        self.left_game_state_queue = left_game_state_queue
        self.right_game_state_queue = right_game_state_queue

        self.scoreboard_font_info = game_render_config.score_board_font
        self.registration_font_info = game_render_config.registration_font
        self.commencement_font_info = game_render_config.commencement_font
        self.fps_font_info = game_render_config.fps_font

        self.registration_font = pygame.font.SysFont(self.registration_font_info.name,
                                                     self.registration_font_info.size,
                                                     self.registration_font_info.is_bold,
                                                     self.registration_font_info.is_italic)

        self.commencement_font = pygame.font.SysFont(self.commencement_font_info.name,
                                                     self.commencement_font_info.size,
                                                     self.commencement_font_info.is_bold,
                                                     self.commencement_font_info.is_italic)

        self.fps_font = pygame.font.SysFont(self.fps_font_info.name,
                                            self.fps_font_info.size,
                                            self.fps_font_info.is_bold,
                                            self.fps_font_info.is_italic)

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

        # specify position of fps counter relative to meta surface
        self.fps_pos = (self.canvas_width - 100, META_DATA_HEIGHT // 2)

        self.game_started: bool = False
        self.registration_closed: bool = False

        # tracks our scoring
        self.scorekeeper: Optional[ScoreKeeper] = None

        # the frame
        self.frame_index: int = 0

        # initial paddle actions
        self.left_paddle_action: Optional[PaddleAction] = None
        self.right_paddle_action: Optional[PaddleAction] = None

    def register_player(self, player: PlayerIdentifier) -> bool:
        """
        :param player:  a player identifier
        :return: True if player successfully registered otherwise false
        """
        with registration_lock:
            if self.game_started:
                logger.warn("Game has already started.  Not taking new registrations")
                return False

            if self.registration_closed:
                logger.warn("Maximum number of players already registered")
                return False

            if player.paddle_type in self.registered_player_by_paddle_type:
                logger.warn(
                    f"Cannot register player {player.player_name}-{player.paddle_strategy_name} because {player.paddle_type} already registered")
                return False

            self.registered_player_by_paddle_type[player.paddle_type] = RegisteredPlayer(player)
            self.cached_score_fonts_by_paddle_type[player.paddle_type] = CachedScoreFontImages()

            for paddle_type, registered_player in self.registered_player_by_paddle_type.items():
                player_info_str = ":".join(
                    (registered_player.player_id.player_name, registered_player.player_id.paddle_strategy_name))
                registration_image = self.registration_font.render(f"Player {player_info_str} has registered",
                                                                   True, self.registration_font_info.color)
                font_pos = self.player_left_registration_pos if paddle_type is PaddleType.LEFT else self.player_right_registration_pos
                self.canvas.blit(registration_image, font_pos)
            self.registration_closed = len(self.registered_player_by_paddle_type) == 2
            pygame.display.update()
            return True

    def render_commencement(self):
        blit_rectangle = None
        for countdown in reversed(range(4)):
            pygame.time.delay(1000)
            commencement_image = self.commencement_font.render(f"Pong Experience Beginning in ... {countdown}",
                                                               True, self.commencement_font_info.color)
            if blit_rectangle:
                self.canvas.fill((0, 0, 0), blit_rectangle)
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
        fps_string = str(int(self.fps_clock.get_fps()))
        fps_image = self.fps_font.render(f"fps: {fps_string}", True, self.fps_font_info.color)
        surface.blit(fps_image, self.fps_pos)
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

    def initialize_paddle_actions(self):
        self.left_paddle_action = PaddleAction(
            player_identifier=self.registered_player_by_paddle_type[PaddleType.LEFT].player_id,
            paddle_directive=PaddleDirective.STATIONARY)

        self.right_paddle_action = PaddleAction(
            player_identifier=self.registered_player_by_paddle_type[PaddleType.RIGHT].player_id,
            paddle_directive=PaddleDirective.STATIONARY)

    def initialize_scoring(self):
        """
        Creates a scorekeeper and also initializes the font images for the scoring surface
        :return:
        """
        registered_player_ids = [player.player_id for player in self.registered_player_by_paddle_type.values()]
        self.scorekeeper = ScoreKeeper(*registered_player_ids)

        for paddle_type, registered_player in self.registered_player_by_paddle_type.items():
            scorecard = self.scorekeeper.get_scorecard(registered_player.player_id)
            self.cached_score_fonts_by_paddle_type[paddle_type].update(scorecard)

    def update_score(self):
        primary_ball_centroid = self.arena.primary_ball.centroid
        left_back_line_centroid = self.arena.left_back_line.centroid
        right_back_line_centroid = self.arena.right_back_line.centroid
        winner_discovered = False
        if primary_ball_centroid[0] < left_back_line_centroid[0]:
            winning_player = self.registered_player_by_paddle_type[PaddleType.RIGHT].player_id
            losing_player = self.registered_player_by_paddle_type[PaddleType.LEFT].player_id
            self.scorekeeper.tally_point(winning_player, losing_player)
            self.cached_score_fonts_by_paddle_type[PaddleType.RIGHT].update(
                self.scorekeeper.get_scorecard(winning_player))
            self.cached_score_fonts_by_paddle_type[PaddleType.LEFT].update(
                self.scorekeeper.get_scorecard(losing_player))
            winner_discovered = True
        elif primary_ball_centroid[0] > right_back_line_centroid[0]:
            winning_player = self.registered_player_by_paddle_type[PaddleType.LEFT].player_id
            losing_player = self.registered_player_by_paddle_type[PaddleType.RIGHT].player_id
            self.scorekeeper.tally_point(winning_player, losing_player)
            self.cached_score_fonts_by_paddle_type[PaddleType.LEFT].update(
                self.scorekeeper.get_scorecard(winning_player))
            self.cached_score_fonts_by_paddle_type[PaddleType.RIGHT].update(
                self.scorekeeper.get_scorecard(losing_player))
            winner_discovered = True

        if winner_discovered:
            self.arena.reset_starting_positions()

    def handle_paddle_actions(self):
        # get actions from the queue.  Oddly have to use exception as case where nothing in queue
        try:
            updated_left_paddle_action: PaddleAction = self.left_paddle_queue.get(timeout=ACTION_QUEUE_TIMEOUT)
        except Empty:
            updated_left_paddle_action = None

        try:
            updated_right_paddle_action: PaddleAction = self.right_paddle_queue.get(timeout=ACTION_QUEUE_TIMEOUT)
        except Empty:
            updated_right_paddle_action = None

        # assign the paddle action to the working action if not None, otherwise working action remains unchanged
        if updated_left_paddle_action: self.left_paddle_action = updated_left_paddle_action
        if updated_right_paddle_action: self.right_paddle_action = updated_right_paddle_action

        # update the velocities on the paddle actors in the arena bases on the paddle action
        left_paddle, right_paddle = self.arena.paddles
        left_paddle.velocity = get_paddle_velocity(self.left_paddle_action.paddle_directive)
        right_paddle.velocity = get_paddle_velocity(self.right_paddle_action.paddle_directive)

    def send_game_state(self):
        builder = GameStateBuilder()
        for actor in self.arena.actors: builder.add_game_actor(actor)
        builder.add_state_iteration(self.frame_index)
        game_state = builder.build()
        self.left_game_state_queue.put(game_state)
        self.right_game_state_queue.put(game_state)

    def start_game(self):
        with game_lock:
            if not self.registration_closed:
                logger.warn("Game cannot start until all players are registered")
                return

            if self.game_started:
                logger.warn("Game is already started!")
                return
            self.game_started = True

        logger.info("GAME COMMENCING")
        self.initialize_paddle_actions()
        self.initialize_scoring()
        self.render_commencement()
        self.fps_clock = pygame.time.Clock()
        pygame.display.update(self.update_panes())

        logger.debug("Sending first game state")
        self.send_game_state()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            logger.debug("Getting paddle actions")
            self.handle_paddle_actions()

            logger.debug("Updating game state")
            self.game_engine.update_state(self.arena.actors)
            pygame.display.update(self.update_panes())
            self.update_score()
            self.frame_index += 1
            self.send_game_state()
            self.fps_clock.tick(FPS_CAP)
