import math
from typing import Callable

import numpy
import shapely
from dependency_injector.providers import DelegatedCallable
from shapely import ops

from config import logging_configurator, property_configurator
from gameengine.collision_engine import ActorPairCollidor
from gameengine.gameactors import Ball, Paddle, BallColor

logger = logging_configurator.get_logger(__name__)
MAX_ANGLE = property_configurator.ball_paddle_collision_config.max_angle_quantity


def update_white_ball(ball: Ball, paddle: Paddle):
    actors_intersect = ball.shape.intersects(paddle.shape)
    if not actors_intersect:
        return

    logger.info(f"Begin classic pong paddle ball collision modeling for {ball.color} and {paddle.name}")
    # lets make ball back up so it is not intersecting anymore.  We will try to back up one pixel at a time
    ball_backup_distance = 1. / numpy.linalg.norm(ball.velocity)
    while actors_intersect:
        logger.info("Moving ball backwards one pixel at a time")
        ball.move_backward(ball_backup_distance)
        actors_intersect = ball.shape.intersects(paddle.shape)
    logger.info("Ball no longer intsersects paddle")

    nearest_ball_point, nearest_poly_point = shapely.ops.nearest_points(ball.shape, paddle.shape)
    paddle_hit_x, paddle_hit_y = nearest_poly_point

    paddle_min_x, paddle_min_y, paddle_max_x, paddle_max_y = paddle.shape.bounds
    paddle_half_lenth = (paddle_max_y - paddle_min_y) / 2.0
    _, paddle_mid_y = paddle.shape.centroid
    hit_distance_from_center = math.fabs(paddle_hit_y - paddle_mid_y)
    normalized_hit_distance_from_center = sorted([0, hit_distance_from_center / paddle_half_lenth, 1])[1]
    rebound_angle = MAX_ANGLE * normalized_hit_distance_from_center

    ball_vel_mag = numpy.linalg.norm(ball.velocity)
    rebound_vel_x = ball_vel_mag * math.cos(rebound_angle.to_base_units().magnitude)
    rebound_vel_x = rebound_vel_x if ball.velocity[0] < 0 else -rebound_vel_x

    rebound_vel_y = ball_vel_mag * math.sin(rebound_angle.to_base_units().magnitude)
    rebound_vel_y = -rebound_vel_y if paddle_hit_y < paddle_mid_y else rebound_vel_y
    ball.velocity = numpy.array([rebound_vel_x, rebound_vel_y])


class CollisionStrategyByColor:
    def __init__(self, white_ball_callable_provider: DelegatedCallable):
        self.white_ball_callable_provider = white_ball_callable_provider

    def provide_callable(self, ball_color: BallColor) -> Callable:
        if ball_color is BallColor.WHITE:
            return self.white_ball_callable_provider
        else:
            return lambda *args: None


class BallPaddleCollider(ActorPairCollidor):
    """
    Models a classic pong paddle whereby if the ball hits the upper part of the paddle is will rebound upward and
    if it hits the bottom part of the paddle it will rebound downward
    """

    def __init__(self, classic_paddle_collision_factory: CollisionStrategyByColor):
        self.classic_paddle_collision_factory = classic_paddle_collision_factory

    def update_pair_state(self, ball: Ball, paddle: Paddle):
        if not isinstance(ball, Ball) or not isinstance(paddle, Paddle):
            return
        collision_strategy_callable = self.classic_paddle_collision_factory.provide_callable(ball.color)
        collision_strategy_callable()
