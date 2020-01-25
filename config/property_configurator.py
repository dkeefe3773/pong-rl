from configparser import ConfigParser
from pathlib import Path
from typing import Any, Tuple

from config.aggregates import FontConfig, ColorConfig
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
        return Config.get_property_int('game_arena', 'paddle_thickness')

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
        return Config.get_property_int('game_arena', 'max_ball_starting_angle_degrees') * ureg.angular_degree

    @property
    def starting_ball_speed(self) -> int:
        return Config.get_property_int('game_arena', 'starting_ball_speed')

    @property
    def arena_width(self) -> int:
        return Config.get_property_int('game_arena', 'arena_width')

    @property
    def arena_height(self) -> int:
        return Config.get_property_int('game_arena', 'arena_height')

    @property
    def wall_thickness(self) -> int:
        return Config.get_property_int('game_arena', 'wall_thickness')


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

    @property
    def default_paddle_speed(self) -> int:
        """
        :return:  The standard speed of the paddle
        """
        return Config.get_property_int('game_engine', 'default_paddle_speed')


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
    def score_board_font(self) -> FontConfig:
        """
        :return:  A FontConfig object for any text in the scoreboard area
        """
        font_name = Config.get_property_string('game_renderer', 'score_board_font_name')
        font_size = Config.get_property_int('game_renderer', 'score_board_font_size')
        font_color = eval(Config.get_property_string('game_renderer', 'score_board_font_color'))
        font_style_bold = Config.get_property_bool('game_renderer', 'score_board_font_bold')
        font_style_italic = Config.get_property_bool('game_renderer', 'score_board_font_italic')
        return FontConfig(font_name, font_size, font_color, font_style_bold, font_style_italic)

    @property
    def registration_font(self) -> FontConfig:
        """
        :return:  A FontConfig object for the textual player registration notices
        """
        font_name = Config.get_property_string('game_renderer', 'registration_font_name')
        font_size = Config.get_property_int('game_renderer', 'registration_font_size')
        font_color = eval(Config.get_property_string('game_renderer', 'registration_font_color'))
        font_style_bold = Config.get_property_bool('game_renderer', 'registration_font_bold')
        font_style_italic = Config.get_property_bool('game_renderer', 'registration_font_italic')
        return FontConfig(font_name, font_size, font_color, font_style_bold, font_style_italic)

    @property
    def commencement_font(self) -> FontConfig:
        """
        :return:  A FontConfig object for the textual game commencement notice
        """
        font_name = Config.get_property_string('game_renderer', 'commencement_font_name')
        font_size = Config.get_property_int('game_renderer', 'commencement_font_size')
        font_color = eval(Config.get_property_string('game_renderer', 'commencement_font_color'))
        font_style_bold = Config.get_property_bool('game_renderer', 'commencement_font_bold')
        font_style_italic = Config.get_property_bool('game_renderer', 'commencement_font_italic')
        return FontConfig(font_name, font_size, font_color, font_style_bold, font_style_italic)

    @property
    def fps_font(self) -> FontConfig:
        """
        :return:  A FontConfig object for the in-game fps counter
        """
        font_name = Config.get_property_string('game_renderer', 'fps_font_name')
        font_size = Config.get_property_int('game_renderer', 'fps_font_size')
        font_color = eval(Config.get_property_string('game_renderer', 'fps_font_color'))
        font_style_bold = Config.get_property_bool('game_renderer', 'fps_font_bold')
        font_style_italic = Config.get_property_bool('game_renderer', 'fps_font_italic')
        return FontConfig(font_name, font_size, font_color, font_style_bold, font_style_italic)

    @property
    def color_config(self) -> ColorConfig:
        score_color = eval(Config.get_property_string('game_renderer', 'score_pane_color'))
        meta_color = eval(Config.get_property_string('game_renderer', 'meta_pane_color'))
        arena_color = eval(Config.get_property_string('game_renderer', 'arena_pane_color'))
        paddle_color = eval(Config.get_property_string('game_renderer', 'paddle_color'))
        obstacle_color = eval(Config.get_property_string('game_renderer', 'obstacle_color'))
        net_color = eval(Config.get_property_string('game_renderer', 'net_color'))
        backline_color = eval(Config.get_property_string('game_renderer', 'backline_color'))
        primary_ball_color = eval(Config.get_property_string('game_renderer', 'primary_ball_color'))
        grow_paddle_ball_color = eval(Config.get_property_string('game_renderer', 'grow_paddle_ball_color'))
        shrink_paddle_ball_color = eval(Config.get_property_string('game_renderer', 'shrink_paddle_ball_color'))
        return ColorConfig(score_color, meta_color, arena_color, paddle_color, primary_ball_color,
                           grow_paddle_ball_color, shrink_paddle_ball_color, net_color, backline_color, obstacle_color)

    @property
    def fps_cap(self) -> int:
        return Config.get_property_int('game_renderer', 'fps_cap')

    @property
    def score_board_height(self) -> int:
        return Config.get_property_int('game_renderer', 'score_board_pane_height')

    @property
    def meta_board_height(self) -> int:
        return Config.get_property_int('game_renderer', 'meta_data_pane_height')

    @property
    def generic_spacer(self) -> int:
        return Config.get_property_int('game_renderer', 'generic_spacer')



class MatchPlayConfig(Config):
    @property
    def points_per_match(self) -> int:
        return Config.get_property_int('match_play', 'points_in_match')

    @property
    def hits_for_draw(self) -> int:
        return Config.get_property_int('match_play', 'hits_for_draw')


class ServerClientCommunicationConfig(Config):
    @property
    def is_client_response_lock(self) -> bool:
        return Config.get_property_bool('server_client_communication', 'block_client_paddle_response')


game_server_config = GameServerConfig()
player_config = PlayerConfig()
game_engine_config = GameEngineConfig()
ball_paddle_collision_config = ClassicPongCollisionConfig()
game_arena_config = GameArenaConfig()
game_render_config = GameRendererConfig()
match_play_config = MatchPlayConfig()
server_client_communication_config = ServerClientCommunicationConfig()
