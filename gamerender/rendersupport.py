from __future__ import annotations

from collections import namedtuple
from enum import Enum
from queue import Empty
from threading import RLock
from typing import TYPE_CHECKING, List, Tuple, Optional

import pygame
from shapely.geometry import Polygon

from config import logging_configurator
from config.property_configurator import game_render_config, server_client_communication_config, game_engine_config, \
    match_play_config
from gameengine.gameactors import Ball, BallFlavor, Actor, Paddle, Net, BackLine
from gamerender.caches import CachedScoreFontImages
from proto_gen.gamemaster_pb2 import PaddleType, PaddleAction, PaddleDirective, PlayerIdentifier

if TYPE_CHECKING:
    from gamerender.pongrenders import DefaultPongRenderer

color_config = game_render_config.color_config

logger = logging_configurator.get_logger(__name__)

# player_id is expected to be PlayerIdentifer object and scorecard a StandardScoreCard
RegisteredPlayer = namedtuple("RegisteredPlayer", ['player_id'])


def color_from_ball(actor: Ball) -> Tuple[int, int, int]:
    if actor.flavor is BallFlavor.PRIMARY:
        color = color_config.primary_ball_color
    elif actor.flavor is BallFlavor.GROW_PADDLE:
        color = color_config.grow_paddle_ball_color
    elif actor.flavor is BallFlavor.SHRINK_PADDLE:
        color = color_config.shrink_paddle_ball_color
    else:
        color = (0, 0, 0)
    return color


def color_from_actor(actor: Actor) -> Tuple[int, int, int]:
    if isinstance(actor, Paddle):
        color = color_config.paddle_color
    elif isinstance(actor, Ball):
        color = color_from_ball(actor)
    elif isinstance(actor, Net):
        color = color_config.net_color
    elif isinstance(actor, BackLine):
        color = color_config.backline_color
    else:
        color = color_config.obstacle_color
    return color


PADDLE_QUEUE_BLOCK = server_client_communication_config.is_client_response_lock
DEFAULT_PADDLE_SPEED = game_engine_config.default_paddle_speed

paddle_directive_to_velocity = {
    PaddleDirective.UP: (0, -DEFAULT_PADDLE_SPEED),
    PaddleDirective.DOWN: (0, DEFAULT_PADDLE_SPEED),
    PaddleDirective.STATIONARY: (0, 0)
    }


def get_paddle_velocity(paddle_directive: PaddleDirective) -> Tuple[int, int]:
    """
    :param paddle_directive:  a directive for paddle direction
    :return:  the velocity as 2-tuple
    """
    return paddle_directive_to_velocity.get(paddle_directive, (0, 0))


class ScorePaneManager:
    def visit(self, pong_renderer: DefaultPongRenderer) -> List[pygame.Rect]:
        """
        This wil blit score changes to the working canvas.
        :return: A list of rectangles that can be used for pygame.display.update that represent
        canvas areas that were updated
        """
        surface = pong_renderer.scoreboard_pane.surface
        left_score_fonts = pong_renderer.cached_score_fonts_by_paddle_type[PaddleType.LEFT]
        right_score_fonts = pong_renderer.cached_score_fonts_by_paddle_type[PaddleType.RIGHT]
        if not left_score_fonts.is_updated or not right_score_fonts.is_updated:
            return []

        # wipe out what was there before
        surface.fill(color_config.score_color)
        spacer = pong_renderer.scoreboard_font_info.size + game_render_config.generic_spacer

        # populate left hand side
        x_start = 0
        y_start = game_render_config.generic_spacer
        for font_image in left_score_fonts.ordered_images():
            surface.blit(font_image, (x_start, y_start))
            y_start += spacer

        # populate right hand side
        x_start = pong_renderer.canvas_width // 2 + game_render_config.generic_spacer
        y_start = game_render_config.generic_spacer
        for font_image in right_score_fonts.ordered_images():
            surface.blit(font_image, (x_start, y_start))
            y_start += spacer
        return [pong_renderer.canvas.blit(surface, pong_renderer.scoreboard_pane.pos)]


class MetaPaneManager:
    def visit(self, pong_renderer: DefaultPongRenderer) -> List[pygame.Rect]:
        """
        This wil blit score changes to the working canvas.
        :return: A list of rectangles that can be used for pygame.display.update that represent
        canvas areas that were updated
        """
        surface = pong_renderer.metadata_pane.surface
        surface.fill(color_config.meta_color)
        fps_string = str(int(pong_renderer.fps_clock.get_fps()))
        fps_image = pong_renderer.fps_font.render(f"fps: {fps_string}", True, pong_renderer.fps_font_info.color)
        surface.blit(fps_image, pong_renderer.fps_pos)
        return [pong_renderer.canvas.blit(surface, pong_renderer.metadata_pane.pos)]


class ArenaPaneManager:
    def visit(self, pong_renderer: DefaultPongRenderer) -> List[pygame.Rect]:
        """
        This wil blit score changes to the working canvas.
        :return: A list of rectangles that can be used for pygame.display.update that represent
        canvas areas that were updated
        """
        surface = pong_renderer.arena_pane.surface
        surface.fill(color_config.arena_color)
        for actor in pong_renderer.arena.actors:
            color = color_from_actor(actor)
            shape: Polygon = actor.shape
            coords = list(shape.exterior.coords)
            pygame.draw.polygon(surface, color, coords)
        return [pong_renderer.canvas.blit(surface, pong_renderer.arena_pane.pos)]


class PaddleManager:
    def visit(self, pong_renderer: DefaultPongRenderer):
        # get actions from the queue.  Oddly have to use exception as case where nothing in queue
        try:
            updated_left_paddle_action: PaddleAction = pong_renderer.left_paddle_queue.get(block=PADDLE_QUEUE_BLOCK)
        except Empty:
            updated_left_paddle_action = None

        try:
            updated_right_paddle_action: PaddleAction = pong_renderer.right_paddle_queue.get(block=PADDLE_QUEUE_BLOCK)
        except Empty:
            updated_right_paddle_action = None

        # assign the paddle action to the working action if not None, otherwise working action remains unchanged
        if updated_left_paddle_action: pong_renderer.left_paddle_action = updated_left_paddle_action
        if updated_right_paddle_action: pong_renderer.right_paddle_action = updated_right_paddle_action

        # update the velocities on the paddle actors in the arena bases on the paddle action
        left_paddle, right_paddle = pong_renderer.arena.paddles
        left_paddle.velocity = get_paddle_velocity(pong_renderer.left_paddle_action.paddle_directive)
        right_paddle.velocity = get_paddle_velocity(pong_renderer.right_paddle_action.paddle_directive)


registration_lock = RLock()


class RegistrationManager:
    def __init__(self):
        self.game_started: bool = False
        self.registration_closed: bool = False

    def register_player(self, pong_renderer: DefaultPongRenderer, player: PlayerIdentifier) -> bool:
        """
        :param player:  a player identifier
        :return: True if player successfully registered otherwise false
        """
        with registration_lock:
            if self.game_started:
                logger.warn("Game has already started.  Not taking new registrations")
                return False

            if self.registration_closed:
                logger.warn("Maximum number of players already registered")
                return False

            if player.paddle_type in pong_renderer.registered_player_by_paddle_type:
                logger.warn(
                    f"Cannot register player {player.player_name}-{player.paddle_strategy_name} because {player.paddle_type} already registered")
                return False

            pong_renderer.registered_player_by_paddle_type[player.paddle_type] = RegisteredPlayer(player)
            pong_renderer.cached_score_fonts_by_paddle_type[player.paddle_type] = CachedScoreFontImages()

            for paddle_type, registered_player in pong_renderer.registered_player_by_paddle_type.items():
                player_info_str = ":".join(
                    (registered_player.player_id.player_name, registered_player.player_id.paddle_strategy_name))
                registration_image = pong_renderer.registration_font.render(f"Player {player_info_str} has registered",
                                                                            True,
                                                                            pong_renderer.registration_font_info.color)
                font_pos = pong_renderer.player_left_registration_pos if paddle_type is PaddleType.LEFT else pong_renderer.player_right_registration_pos
                pong_renderer.canvas.blit(registration_image, font_pos)
            self.registration_closed = len(pong_renderer.registered_player_by_paddle_type) == 2
            pygame.display.update()
            return True


class Direction(Enum):
    UNSET = 1
    LEFT = 2
    RIGHT = 3


class ScoringManager:
    def __init__(self):
        self.change_of_direction_count: int = 0
        self.last_ball_dirction: Optional[Direction] = Direction.UNSET

    def update_score(self, pong_renderer: DefaultPongRenderer):
        current_ball_direction = Direction.RIGHT if pong_renderer.arena.primary_ball.velocity[0] > 0 else Direction.LEFT
        if self.last_ball_dirction is Direction.UNSET:
            self.last_ball_dirction = current_ball_direction

        if self.last_ball_dirction is not current_ball_direction:
            self.change_of_direction_count += 1
            self.last_ball_dirction = current_ball_direction

        primary_ball_centroid = pong_renderer.arena.primary_ball.centroid
        left_back_line_centroid = pong_renderer.arena.left_back_line.centroid
        right_back_line_centroid = pong_renderer.arena.right_back_line.centroid
        winner_discovered = False
        if primary_ball_centroid[0] < left_back_line_centroid[0]:
            winning_player = pong_renderer.registered_player_by_paddle_type[PaddleType.RIGHT].player_id
            losing_player = pong_renderer.registered_player_by_paddle_type[PaddleType.LEFT].player_id
            pong_renderer.scorekeeper.tally_point(winning_player, losing_player)
            pong_renderer.cached_score_fonts_by_paddle_type[PaddleType.RIGHT].update(
                pong_renderer.scorekeeper.get_scorecard(winning_player))
            pong_renderer.cached_score_fonts_by_paddle_type[PaddleType.LEFT].update(
                pong_renderer.scorekeeper.get_scorecard(losing_player))
            winner_discovered = True
        elif primary_ball_centroid[0] > right_back_line_centroid[0]:
            winning_player = pong_renderer.registered_player_by_paddle_type[PaddleType.LEFT].player_id
            losing_player = pong_renderer.registered_player_by_paddle_type[PaddleType.RIGHT].player_id
            pong_renderer.scorekeeper.tally_point(winning_player, losing_player)
            pong_renderer.cached_score_fonts_by_paddle_type[PaddleType.LEFT].update(
                pong_renderer.scorekeeper.get_scorecard(winning_player))
            pong_renderer.cached_score_fonts_by_paddle_type[PaddleType.RIGHT].update(
                pong_renderer.scorekeeper.get_scorecard(losing_player))
            winner_discovered = True

        if winner_discovered:
            self.change_of_direction_count = 0
            self.last_ball_dirction = Direction.UNSET
            pong_renderer.arena.reset_starting_positions()

        elif self.change_of_direction_count >= match_play_config.hits_for_draw:
            self.change_of_direction_count = 0
            self.last_ball_dirction = Direction.UNSET
            pong_renderer.scorekeeper.tally_aborted_point()
            for score_font_cache in pong_renderer.cached_score_fonts_by_paddle_type.values():
                score_font_cache.points_drawn = score_font_cache.points_drawn + 1
            pong_renderer.arena.reset_starting_positions()
