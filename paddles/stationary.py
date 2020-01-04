from config import logging_configurator
from paddles.paddle import PaddleController
from proto_gen.gamemaster_pb2 import GameState, PaddleAction

logger = logging_configurator.get_logger(__name__)


class StationaryPaddle(PaddleController):
    def process_game_state(self, game_state: GameState):
        logger.info("Processing game state {}".format(game_state.state_iteration))
        return PaddleAction()
