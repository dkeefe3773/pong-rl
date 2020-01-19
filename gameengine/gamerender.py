import sys
from threading import RLock

import pygame
# initialize pygame modules
from pygame import font
from pygame import surfarray

from config import logging_configurator
from config.property_configurator import game_render_config
from gameengine.arena import Arena
from proto_gen.gamemaster_pb2 import PlayerIdentifier, PaddleType

logger = logging_configurator.get_logger(__name__)

# a puzzling requirement for 'initializing' all the pygame modules.
# apparently, if performance is an issue, you just initialize the modules you need, but not a problem right now
pygame.init()

SCORE_BOARD_HEIGHT = 200
REGISTRATION_OFFSET = 50

registration_lock = RLock()
game_lock = RLock()
pygame.display.set_caption("Pong is only for the brave")

class PongRenderer:
    def __init__(self, arena: Arena):
        scoreboard_font_name, scoreboard_font_size, self.scoreboard_font_color = \
            game_render_config.score_board_font
        registration_font_name, registration_font_size, self.registration_font_color = \
            game_render_config.registration_font

        self.scoreboard_font = pygame.font.SysFont(name=scoreboard_font_name,
                                                   size=scoreboard_font_size)

        self.registration_font = pygame.font.SysFont(name=registration_font_name,
                                                     size=registration_font_size)

        self.arena = arena
        self.canvas = pygame.display.set_mode([arena.arena_width, arena.arena_height + SCORE_BOARD_HEIGHT])
        self.scoreboard_surface = pygame.Surface((arena.arena_width, SCORE_BOARD_HEIGHT))
        self.cached_scoreboard_fonts = {}  # key is font, value is placement
        self.cached_player_registration_fonts = {}  # key is font , value is placement
        self.registered_player_by_id = {}  # key is concat(name, strategy) and value is player identifier

        # specify positions for the registration notifications
        self.player_left_registration_pos = ((REGISTRATION_OFFSET, arena.arena_height // 2))
        self.player_right_registration_pos = ((arena.arena_width // 2 + REGISTRATION_OFFSET, arena.arena_height // 2))
        self.game_started: bool = False
        self.registration_closed: bool = False

    def score_board_setup(self, player_one: PlayerIdentifier, player_two: PlayerIdentifier):
        pass

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
                                                                   color=self.registration_font_color)
                font_pos = self.player_left_registration_pos if player_id.paddle_type is PaddleType.LEFT \
                    else self.player_right_registration_pos
                self.canvas.blit(registration_image, font_pos)
            self.registration_closed = len(self.registered_player_by_id) == 2
            pygame.display.update()

    def draw_arena(self, screen):
        black = (0, 0, 0)
        white = (255, 255, 255)
        screen.fill(black)
        pygame.draw.rect(screen, white, ((0, 0), (self.screen_width, self.screen_height)), 20)

    def render_commencement(self):


    def start_game(self, player_one: PlayerIdentifier, player_two: PlayerIdentifier):
        with game_lock:
            if not self.registration_closed:
                logger.warn("Game cannot start until all players are registered")
                return

            if self.game_started:
                logger.warn("Game is already started!")
                return
            self.game_started = True
        fps_clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.draw_arena(screen)

            fps = self.fps_font.render(str(int(fps_clock.get_fps())), True, pygame.Color('white'))
            self.canvas.blit(fps, (50, 50))
            pygame.display.update()

            screen_array = surfarray.array3d(screen)

            fps_clock.tick(24)


if __name__ == "__main__":
    pong_renderer = PongRenderer()
    pong_renderer.start_game()
