from abc import ABC, abstractmethod
from typing import Optional

from config import logging_configurator
from proto_gen.gamemaster_pb2 import GameState, PaddleAction

logger = logging_configurator.get_logger(__name__)


class PaddleController(ABC):
    @abstractmethod
    def process_game_state(self, game_state: GameState) -> Optional[PaddleAction]:
        """
        :param game_state: the state of the game
        :return: A paddle Action object or None for no action
        """
        pass
