import time

from gamerender.pongrenders import DefaultPongRenderer
from injections import providers
from proto_gen.gamemaster_pb2 import PlayerIdentifier, PaddleType


def test_game_render():
    player_left_identifier = PlayerIdentifier(player_name="LEFT_PLAYER",
                                              paddle_strategy_name="LEFT_STRATEGY",
                                              paddle_type=PaddleType.LEFT)

    player_right_identifier = PlayerIdentifier(player_name="RIGHT_PLAYER",
                                               paddle_strategy_name="RIGHT_STRATEGY",
                                               paddle_type=PaddleType.RIGHT)

    pong_renderer: DefaultPongRenderer = providers.GameRendererProviders.pong_renderer()

    pong_renderer.register_player(player_left_identifier)

    time.sleep(1)

    pong_renderer.register_player(player_right_identifier)

    time.sleep(1)

    pong_renderer.start_game()


if __name__ == "__main__":
    test_game_render()
