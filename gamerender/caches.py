from typing import Optional, List

import pygame
from pygame.time import Clock

from config.property_configurator import game_render_config
from gamerender.scorecards import StandardScoreCard


class CachedScoreFontImages:
    """
    This class is for storing fonts and their derived images for the game scoreboard.
    """

    def __init__(self):
        self.fontconfig = game_render_config.score_board_font
        self.font = pygame.font.SysFont(self.fontconfig.name,
                                        self.fontconfig.size,
                                        self.fontconfig.is_bold,
                                        self.fontconfig.is_italic)
        self._player_name: Optional[str] = None
        self._paddle_strategy_name: Optional[str] = None
        self._match_points: Optional[int] = None
        self._total_points: Optional[int] = None
        self._matches_won: Optional[int] = None
        self.name_image: Optional[pygame.Surface] = None
        self.paddle_stategy_image: Optional[pygame.Surface] = None
        self.match_points_image: Optional[pygame.Surface] = None
        self.total_points_image: Optional[pygame.Surface] = None
        self.matches_won_image: Optional[pygame.Surface] = None
        self.fps_clock: Optional[Clock] = None

    def ordered_images(self) -> List[pygame.Surface]:
        return [self.name_image, self.paddle_stategy_image, self.match_points_image, self.total_points_image,
                self.matches_won_image]

    @property
    def is_updated(self):
        return self._image_updated

    @property
    def player_name(self) -> str:
        return self._player_name

    @player_name.setter
    def player_name(self, name: str):
        if name != self._player_name:
            self._player_name = name
            self._update_name_image()
            self._image_updated = True

    @property
    def paddle_strategy_name(self) -> str:
        return self._paddle_strategy_name

    @paddle_strategy_name.setter
    def paddle_strategy_name(self, name):
        if name != self._paddle_strategy_name:
            self._paddle_strategy_name = name
            self._update_strategy_image()
            self._image_updated = True

    @property
    def match_points(self) -> int:
        return self._match_points

    @match_points.setter
    def match_points(self, points: int):
        if points != self._match_points:
            self._match_points = points
            self._update_match_points_image()
            self._image_updated = True

    @property
    def total_points(self) -> int:
        return self._total_points

    @total_points.setter
    def total_points(self, points: int):
        if points != self._total_points:
            self._total_points = points
            self._update_total_points_image()
            self._image_updated = True

    @property
    def matches_won(self) -> int:
        return self._matches_won

    @matches_won.setter
    def matches_won(self, count: int):
        if count != self._matches_won:
            self._matches_won = count
            self._update_matches_won_image()
            self._image_updated = True

    def update(self, scorecard: StandardScoreCard):
        self.image_updated = False
        self.player_name = scorecard.player_identifier.player_name
        self.paddle_strategy_name = scorecard.player_identifier.paddle_strategy_name
        self.match_points = scorecard.match_score
        self.total_points = scorecard.total_points
        self.matches_won = scorecard.total_matches

    def _update_name_image(self):
        self.name_image = self.font.render(f"Player Name: {self.player_name}", True, self.fontconfig.color)

    def _update_strategy_image(self):
        self.paddle_stategy_image = self.font.render(f"Paddle Strategy: {self.paddle_strategy_name}", True,
                                                     self.fontconfig.color)

    def _update_match_points_image(self):
        self.match_points_image = self.font.render(f"Match Points: {self.match_points}", True, self.fontconfig.color)

    def _update_total_points_image(self):
        self.total_points_image = self.font.render(f"Total Points: {self.total_points}", True, self.fontconfig.color)

    def _update_matches_won_image(self):
        self.matches_won_image = self.font.render(f"Match Count: {self.matches_won}", True, self.fontconfig.color)
