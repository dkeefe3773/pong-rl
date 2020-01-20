from typing import Tuple


class FontConfig:
    def __init__(self, name: str = "Helvitica", size: int = 30, color: Tuple[int, int, int] = (255, 255, 255),
                 bold: bool = False, italic: bool = False):
        self.name = name
        self.size = size
        self.color = color
        self._bold = bold
        self._italic = italic

    @property
    def is_italic(self):
        return self._italic

    @property
    def is_bold(self):
        return self._bold


class ColorConfig:
    def __init__(self, score_color: Tuple[int, int, int] = (255, 255, 255),
                 meta_color: Tuple[int, int, int] = (255, 255, 255),
                 arena_color: Tuple[int, int, int] = (255, 255, 255),
                 paddle_color: Tuple[int, int, int] = (0, 0, 0),
                 primary_ball_color: Tuple[int, int, int] = (0, 0, 0),
                 net_color: Tuple[int, int, int] = (0, 0, 0),
                 obstacle_color: Tuple[int, int, int] = (0, 0, 0)):
        self.score_color = score_color
        self.meta_color = meta_color
        self.arena_color = arena_color
        self.paddle_color = paddle_color
        self.primary_ball_color = primary_ball_color
        self.net_color = net_color
        self.obstacle_color = obstacle_color
