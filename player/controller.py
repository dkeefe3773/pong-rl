import threading
from datetime import datetime, timezone
from queue import Queue

from config import logging_configurator
from paddles.paddle import PaddleController
from player import serverstub
from proto_gen.gamemaster_pb2 import PlayerIdentifier, PaddleType

logger = logging_configurator.get_logger(__name__)

paddle_action_queue = Queue()
_stop_providing_actions = threading.Event()


def paddle_action_provider():
    while not _stop_providing_actions.is_set():
        paddle_action = None
        try:
            paddle_action = paddle_action_queue.get(block=True, timeout=10)
        except:
            pass
        if paddle_action is not None:
            logger.info("Yielding paddle action")
            yield paddle_action
        else:
            logger.info("No paddle action generated during timeout period")
    logger.info("Paddle actions are no longer being served")


class PlayerController:
    def __init__(self, name: str, paddle_type: PaddleType, paddle_controller: PaddleController):
        """

        :param name:                 player name
        :param paddle_type:          left or right
        :param paddle_controller:    the strategy for moving the paddle
        """
        self.paddle_controller = paddle_controller
        self.player_identifier: PlayerIdentifier = PlayerIdentifier(player_name=name, paddle_type=paddle_type,
                                                                    paddle_strategy_name=paddle_controller.__class__.__name__)

    def start_playing(self):
        self._register()
        self._process_game_state()

    def _register(self):
        serverstub.register_player(self.player_identifier)
        serverstub.submit_paddle_action_iterator(paddle_action_provider())

    def _process_game_state(self):
        for game_state in serverstub.serve_game_states(self.player_identifier):
            utc_time: datetime = game_state.state_time.ToDatetime()
            local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
            logger.info("Received game state {} from server at time {}".format(game_state.state_iteration, local_time))
            if not game_state.HasField("winning_player"):
                paddle_action = self.paddle_controller.process_game_state(game_state)
                if paddle_action is not None:
                    paddle_action.player_identifier.CopyFrom(self.player_identifier)
                    paddle_action_queue.put(paddle_action)
            else:
                logger.info("Winner!  Game Over")
                _stop_providing_actions.set()
