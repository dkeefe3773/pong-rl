# to get rid of alsa sound errors: see https://raspberrypi.stackexchange.com/questions/83254/pygame-and-alsa-lib-error
import os
import sys
from queue import Queue

from pygame.time import Clock

from gamerender.caches import CachedScoreFontImages
from gamerender.rendersupport import ScorePaneManager, MetaPaneManager, ArenaPaneManager, PaddleManager, \
    RegistrationManager, RegisteredPlayer, ScoringManager
from translators.proto_translations import GameStateBuilder

os.environ['SDL_AUDIODRIVER'] = 'dsp'

from collections import namedtuple
from threading import RLock
from typing import Dict, List, Optional

import pygame
from pygame import font

from config import logging_configurator
from config.property_configurator import game_render_config
from gameengine.arena import Arena
from gameengine.collision_engine import GameCollisionEngine
from gamerender.scorecards import ScoreKeeper
from proto_gen.gamemaster_pb2 import PlayerIdentifier, PaddleType, PaddleAction, PaddleDirective

logger = logging_configurator.get_logger(__name__)
color_config = game_render_config.color_config

# a puzzling requirement for 'initializing' all the pygame modules.
# apparently, if performance is an issue, you just initialize the modules you need, but not a problem right now
pygame.init()

REGISTRATION_OFFSET_HORIZ: int = 10

game_lock = RLock()
pygame.display.set_caption("Pong!")

# surface is expected to be a pygame surface and pos is (x,y) of where surface is to be rendered on the canvas
GamePane = namedtuple("GamePane", ['surface', 'pos'])

# game is capped at this fps
FPS_CAP: int = game_render_config.fps_cap


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
        self.score_pane_manager = ScorePaneManager()
        self.meta_pane_manager = MetaPaneManager()
        self.arena_pane_manager = ArenaPaneManager()
        self.paddle_manager = PaddleManager()
        self.registration_manager = RegistrationManager()
        self.scoring_manager = ScoringManager()

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
        self.canvas_height = game_render_config.score_board_height + game_render_config.generic_spacer + \
                             game_render_config.meta_board_height + game_render_config.generic_spacer + \
                             self.arena.arena_height + game_render_config.generic_spacer
        self.canvas = pygame.display.set_mode([self.canvas_width, self.canvas_height], depth=32)

        # create the scoreboard surface, meta-data surface, and arena surface and record their positions on the canvas
        score_y_pos = 0
        metadata_y_pos = score_y_pos + game_render_config.score_board_height + game_render_config.generic_spacer
        arena_y_pos = metadata_y_pos + game_render_config.meta_board_height + game_render_config.generic_spacer
        self.scoreboard_pane = GamePane(pygame.Surface((self.arena.arena_width, game_render_config.score_board_height)),
                                        (0, score_y_pos))
        self.metadata_pane = GamePane(pygame.Surface((self.arena.arena_width, game_render_config.meta_board_height)),
                                      (0, metadata_y_pos))
        self.arena_pane = GamePane(pygame.Surface((self.arena.arena_width, self.arena.arena_height)), (0, arena_y_pos))

        # dict to track registerd players.  key is paddle type and value is registered player
        self.registered_player_by_paddle_type: Dict[PaddleType, RegisteredPlayer] = {}
        self.cached_score_fonts_by_paddle_type: Dict[PaddleType, CachedScoreFontImages] = {}

        # specify positions for the registration notifications
        self.player_left_registration_pos = (REGISTRATION_OFFSET_HORIZ, 0)
        self.player_right_registration_pos = (
            REGISTRATION_OFFSET_HORIZ, self.registration_font_info.size + game_render_config.generic_spacer)

        # specify position for game commencement notification
        self.commencement_pos = (0, self.canvas_height // 2)

        # specify position of fps counter relative to meta surface
        self.fps_pos = (
            self.canvas_width - 100, game_render_config.meta_board_height // 2 - self.fps_font_info.size // 4)

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
        return self.registration_manager.register_player(self, player)

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
        blitted_rectangles.extend(self.score_pane_manager.visit(self))
        blitted_rectangles.extend(self.meta_pane_manager.visit(self))
        blitted_rectangles.extend(self.arena_pane_manager.visit(self))
        return blitted_rectangles

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

    def send_game_state(self):
        builder = GameStateBuilder()
        for actor in self.arena.actors: builder.add_game_actor(actor)
        builder.add_state_iteration(self.frame_index)
        builder.add_arena_surface(self.arena_pane.surface)
        builder.add_scorekeeper(self.scorekeeper)
        game_state = builder.build()
        self.left_game_state_queue.put(game_state)
        self.right_game_state_queue.put(game_state)

    def start_game(self):
        with game_lock:
            if not self.registration_manager.registration_closed:
                logger.warn("Game cannot start until all players are registered")
                return

            if self.registration_manager.game_started:
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
            self.paddle_manager.visit(self)

            logger.debug("Updating game state")
            self.game_engine.update_state(self.arena.actors)
            pygame.display.update(self.update_panes())
            self.scoring_manager.update_score(self)
            self.frame_index += 1
            self.send_game_state()
            self.fps_clock.tick(FPS_CAP)
