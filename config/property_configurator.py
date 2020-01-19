from configparser import ConfigParser
from pathlib import Path
from typing import Any, Tuple

from utils.measures import ureg

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

class GameArenaConfig(Config):
   @property
   def paddle_offset(self) -> int:
       return Config.get_property_int('game_arena', 'paddle_offset')

   @property
   def paddle_width(self) -> int:
       return Config.get_property_int('game_arena', 'paddle_width')

   @property
   def paddle_height(self) -> int:
       return Config.get_property_int('game_arena', 'paddle_height')

   @property
   def white_ball_radius(self) -> int:
       return Config.get_property_int('game_arena', 'white_ball_radius')

   @property
   def max_ball_starting_angle(self) -> ureg.Quantity:
       """
       :return: The angle quantity representing the maximum starting angle a ball can have
       """
       return Config.get_property_int('game_arena', 'max_ball_starting_angle_degress') * ureg.angular_degree

   @property
   def starting_ball_speed(self) -> int:
       return Config.get_property_int('game_arena', 'starting_ball_speed')

   @property
   def arena_width(self) -> int:
       return Config.get_property_int('game_arena', 'arena_width')

   @property
   def arena_height(self) -> int:
       return Config.get_property_int('game_arena', 'arena_height')

class GameEngineConfig(Config):
    @property
    def max_speed(self) -> int:
        """
        :return:  The maximum pixels per frame any object in the game can move
        """
        return Config.get_property_int('game_engine', 'max_speed')

    @property
    def min_speed(self) -> int:
        """
        :return:  The minimum pixels per frame any object in the game can move
        """
        return Config.get_property_int('game_engine', 'min_speed')

    @property
    def max_ball_speed(self) -> int:
        """
        :return:  The maximum pixels per frame any ball in the game can move
        """
        return min(Config.get_property_int('game_engine', 'max_ball_speed'), self.max_speed)

    @property
    def max_paddle_speed(self) -> int:
        """
        :return:  The maximum speed any paddle can move in the game
        """
        return min(Config.get_property_int('game_engine', 'max_paddle_speed'), self.max_speed)

    @property
    def min_ball_speed(self) -> int:
        """
        :return:  The minimum pixels per frame any ball in the game can move
        """
        return max(Config.get_property_int('game_engine', 'min_ball_speed'), self.min_speed)

    @property
    def min_paddle_speed(self) -> int:
        """
        :return:  The minimum speed any paddle can move in the game
        """
        return max(Config.get_property_int('game_engine', 'min_paddle_speed'), self.min_speed)



class ClassicPongCollisionConfig(Config):
    @property
    def max_angle_quantity(self) -> ureg.Quantity:
        """
        :return: The angle quantity representing the maximum reflection angle a ball can have off a paddle
        """
        return Config.get_property_float('ball_paddle_collision', 'max_angle_degress') * ureg.angular_degree

class GameRendererConfig(Config):
    @property
    def paddle_color(self) -> Tuple[int, int, int]:
        rgb_string = Config.get_property_string('game_renderer', 'paddle_color')
        return eval(rgb_string)

    @property
    def score_board_font_name(self) -> str:
        return Config.get_property_string('game_renderer', 'score_board_font')

    @property
    def score_board_font(self) -> Tuple[str, int, Tuple[int,int,int]]:
        """
        :return: a 3-tuple (font_name, font_size, font_color)
        """
        font_specifier_string = Config.get_property_string('game_renderer', 'score_board_font')
        return eval(font_specifier_string)

    @property
    def registration_font(self) -> Tuple[str, int, Tuple[int,int,int]]:
        """
        :return: a 3-tuple (font_name, font_size, font_color)
        """
        rgb_string = Config.get_property_string('game_renderer', 'registration_font')
        return eval(rgb_string)


game_server_config = GameServerConfig()
player_config = PlayerConfig()
game_engine_config = GameEngineConfig()
ball_paddle_collision_config = ClassicPongCollisionConfig()
game_arena_config = GameArenaConfig()
game_render_config = GameRendererConfig()
