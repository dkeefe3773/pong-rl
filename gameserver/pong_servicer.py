import queue
import threading
import time
from typing import Generator

from google.protobuf.empty_pb2 import Empty
from google.protobuf.timestamp_pb2 import Timestamp

from config import logging_configurator
from gamerender.pongrenders import DefaultPongRenderer
from proto_gen import gamemaster_pb2_grpc
from proto_gen.gamemaster_pb2 import GameState, PlayerIdentifier, PaddleType, PaddleAction

logger = logging_configurator.get_logger(__name__)


class DefaultPongServicer(gamemaster_pb2_grpc.GameMasterServicer):
    def __init__(self, left_paddle_queue: queue.Queue, right_paddle_queue: queue.Queue,
                 left_game_state_queue: queue.Queue, right_game_state_queue,
                 pong_renderer: DefaultPongRenderer):
        self.left_paddle_queue = left_paddle_queue
        self.right_paddle_queue = right_paddle_queue
        self.left_game_state_queue = left_game_state_queue
        self.right_game_state_queue = right_game_state_queue
        self.pong_renderer = pong_renderer

        self.registered_player_count = 0

    def stream_game_state(self, request: PlayerIdentifier, context) -> Generator[GameState, None, None]:
        if request.paddle_type is PaddleType.LEFT:
            game_state_queue = self.left_game_state_queue
        else:
            game_state_queue = self.right_game_state_queue


        while True:
            game_state = game_state_queue.get() # this will block indefinitely
            logger.debug(
                "Serving game state to [{}:{}]".format(request.player_name, request.paddle_strategy_name))
            yield game_state

    def register_player(self, request, context):
        logger.info("Registering {}:{} controlling the {}".format(request.player_name,
                                                                  request.paddle_strategy_name,
                                                                  request.paddle_type))
        if self.pong_renderer.register_player(request):
            self.registered_player_count += 1

        if self.registered_player_count == 2:
            logger.info("Starting Pong Game on a different thread")
            game_thread = threading.Thread(target = self.pong_renderer.start_game, name = "game_thread")
            game_thread.start()
        return Empty()

    def submit_paddle_actions(self, request_iterator: Generator[PaddleAction, None, None], context):
        for paddle_action in request_iterator:
            player_identifier = paddle_action.player_identifier
            logger.debug("Received paddle action from [{}:{}]".format(player_identifier.player_name,
                                                                     player_identifier.paddle_strategy_name))

            if player_identifier.paddle_type is PaddleType.LEFT:
                self.left_paddle_queue.put(paddle_action)
            elif player_identifier.paddle_type is PaddleType.RIGHT:
                self.right_paddle_queue.put(paddle_action)
        return Empty()

class DummyPongServicer(gamemaster_pb2_grpc.GameMasterServicer):
    """
    Implementation of the APIs of the GameMasterServicer
    This isn't hooked into a game engine is is merely for testing purposes
    """

    def stream_game_state(self, request, context) -> Generator[GameState, None, None]:
        if request.paddle_type is PaddleType.LEFT:
            logger.info("I AM HERE")
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
