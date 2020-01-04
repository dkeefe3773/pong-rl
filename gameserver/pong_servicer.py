import time
from typing import Generator

from google.protobuf.empty_pb2 import Empty
from google.protobuf.timestamp_pb2 import Timestamp

from config import logging_configurator
from proto_gen import gamemaster_pb2_grpc
from proto_gen.gamemaster_pb2 import GameState, PlayerIdentifier

logger = logging_configurator.get_logger(__name__)


class DummyPongServicer(gamemaster_pb2_grpc.GameMasterServicer):
    """
    Implementation of the APIs of the GameMasterServicer
    This isn't hooked into a game engine is is merely for testing purposes
    """

    def stream_game_state(self, request, context) -> Generator[GameState, None, None]:
        counter = 0
        while counter < 30:
            time_stamp = Timestamp()
            time_stamp.GetCurrentTime()
            game_state: GameState = GameState(state_iteration=counter, state_time=time_stamp)
            logger.info(
                "Serving game state {} to [{}:{}]".format(counter, request.player_name,
                                                          request.paddle_strategy_name))
            time.sleep(1)
            yield game_state
            counter += 1
        time_stamp = Timestamp()
        time_stamp.GetCurrentTime()
        yield GameState(winning_player=PlayerIdentifier(player_name="THE WINNER", paddle_strategy_name="THE BEST"),
                        state_iteration=counter + 1, state_time=time_stamp)

    def register_player(self, request, context):
        logger.info("Registering {}:{} controlling the {}".format(request.player_name,
                                                                  request.paddle_strategy_name,
                                                                  request.paddle_type))
        return Empty()

    def submit_paddle_actions(self, request_iterator, context):
        for paddle_action in request_iterator:
            player_identifier = paddle_action.player_identifier
            logger.info("Received paddle action from [{}:{}]".format(player_identifier.player_name,
                                                                     player_identifier.paddle_strategy_name))
        return Empty()
