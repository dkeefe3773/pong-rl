from collections import namedtuple
from threading import RLock

import pygame
# initialize pygame modules
from pygame import font

from config import logging_configurator
from config.property_configurator import game_render_config
from gameengine.arena import Arena
from gameengine.collision_engine import GameCollisionEngine
from proto_gen.gamemaster_pb2 import PlayerIdentifier, PaddleType

logger = logging_configurator.get_logger(__name__)

# a puzzling requirement for 'initializing' all the pygame modules.
# apparently, if performance is an issue, you just initialize the modules you need, but not a problem right now
pygame.init()

SCORE_BOARD_HEIGHT = 200
META_DATA_HEIGHT = 20
REGISTRATION_OFFSET_HORIZ = 50
COMMENCEMENT_OFFSET_VERT = 100
SEPARATOR = 5

registration_lock = RLock()
game_lock = RLock()
pygame.display.set_caption("Pong is only for the brave")

GamePane = namedtuple("GamePane", ['surface', 'pos'])


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
        self.scoreboard_pane = GamePane(pygame.Surface(self.arena.arena_width, SCORE_BOARD_HEIGHT), (0, score_y_pos))
        self.metadata_pane = GamePane(pygame.Surface(self.arena.arena_width, META_DATA_HEIGHT), (0, metadata_y_pos))
        self.arena_pane = GamePane(pygame.Surface(self.arena.arena_width, self.arena.arena_height), (0, arena_y_pos))

        # dict to track registerd players
        self.registered_player_by_id = {}  # key is concat(name, strategy) and value is player identifier

        # specify positions for the registration notifications
        self.player_left_registration_pos = ((REGISTRATION_OFFSET_HORIZ, self.canvas_height // 2))
        self.player_right_registration_pos = (
        (self.canvas_width // 2 + REGISTRATION_OFFSET_HORIZ, self.canvas_height // 2))

        # specify position for game commencement notification
        self.commencement_pos = ((self.canvas_width // 2), self.canvas_height // 2 + COMMENCEMENT_OFFSET_VERT)

        self.game_started: bool = False
        self.registration_closed: bool = False

    def register_player(self, player: PlayerIdentifier):
        with registration_lock:
            player_id = "_".join((player.name, player.paddle_strategy_name))
            if self.game_started:
                logger.warn("Game has already started.  Not taking new registrations")
                return

            if self.registration_closed:
                logger.warn("Maximum number of players already registered")
                return

            if player_id in self.registered_player_by_id:
                logger.warn(f"Player {player.name}-{player.paddle_strategy_name} is already registered")
                return

            self.registered_player_by_id[player_id] = player
            for player_id_key, player_id in self.registered_player_by_id.items():
                registration_image = self.registration_font.render(f"Player {player_id} has registered",
                                                                   color=self.registration_font_info.color)
                font_pos = self.player_left_registration_pos \
                    if player_id.paddle_type is PaddleType.LEFT else self.player_right_registration_pos
                self.canvas.blit(registration_image, font_pos)
            self.registration_closed = len(self.registered_player_by_id) == 2
            pygame.display.update()

    def draw_arena(self, screen):
        pass
        # black = (0, 0, 0)
        # white = (255, 255, 255)
        # screen.fill(black)
        # pygame.draw.rect(screen, white, ((0, 0), (self.screen_width, self.screen_height)), 20)

    def render_commencement(self):
        for countdown in reversed(range(3)):
            commenement_image = self.commencement_font.render(f"Pong Experience Beginning in:   {countdown}",
                                                              color=self.commencement_font_info.color)
            self.canvas.blit(commenement_image, self.commencement_pos)
            pygame.time.delay(1000)

    def update_panes(self):
        pass

    def start_game(self, player_one: PlayerIdentifier, player_two: PlayerIdentifier):
        with game_lock:
            if not self.registration_closed:
                logger.warn("Game cannot start until all players are registered")
                return

            if self.game_started:
                logger.warn("Game is already started!")
                return
            self.game_started = True

        self.render_commencement()
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


if __name__ == "__main__":
    pong_renderer = PongRenderer()
    pong_renderer.start_game()
