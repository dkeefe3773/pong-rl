from configparser import ConfigParser
from pathlib import Path
from typing import Any

true_path = Path(__file__).parent / 'config.ini'
_parser = ConfigParser()
_parser.read(str(true_path.resolve()), encoding='utf-8')


class Config(object):
    @staticmethod
    def get_property_string(section_name: str, property_name: str) -> Any:
        return _parser.get(section_name, property_name)

    @staticmethod
    def get_property_int(section_name: str, property_name: str) -> Any:
        return _parser.getint(section_name, property_name)

    @staticmethod
    def get_property_float(section_name: str, property_name: str) -> Any:
        return _parser.getfloat(section_name, property_name)

    @staticmethod
    def get_property_bool(section_name: str, property_name: str) -> Any:
        return _parser.getboolean(section_name, property_name)


class GameServerConfig(Config):
    @property
    def host(self) -> str:
        return Config.get_property_string('game_master_service', 'host')

    @property
    def port(self) -> str:
        return Config.get_property_string('game_master_service', 'port')

    @property
    def max_workers(self) -> int:
        return Config.get_property_int('game_master_service', 'max_workers')

    @property
    def thread_pool_prefix(self) -> int:
        return Config.get_property_string('game_master_service', 'thread_prefix')


class PlayerConfig(Config):
    @property
    def left_player_name(self) -> str:
        return Config.get_property_string('player', 'left_player_name')

    @property
    def right_player_name(self) -> str:
        return Config.get_property_string('player', 'right_player_name')


game_server_config = GameServerConfig()
player_config = PlayerConfig()
