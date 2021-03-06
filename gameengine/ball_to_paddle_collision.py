import math
from typing import Callable

import shapely
from dependency_injector.providers import DelegatedCallable
from shapely import ops

from config import logging_configurator, property_configurator
from gameengine.collision_engine import ActorPairCollidor
from gameengine.gameactors import Ball, Paddle, BallFlavor

logger = logging_configurator.get_logger(__name__)
MAX_ANGLE = property_configurator.ball_paddle_collision_config.max_angle_quantity


def update_primary_ball(ball: Ball, paddle: Paddle):
    actors_intersect = ball.shape.intersects(paddle.shape)
    if not actors_intersect:
        return

    logger.debug(f"Begin classic pong paddle ball collision modeling for {ball.flavor} and {paddle.name}")
    # lets make ball back up so it is not intersecting anymore.  We will try to back up one pixel at a time
    ball_backup_distance = 1. / ball.vnorm
    while actors_intersect:
        logger.debug("Moving ball backwards one pixel at a time")
        ball.move_backward(ball_backup_distance)
        actors_intersect = ball.shape.intersects(paddle.shape)
    logger.debug("Ball no longer intsersects paddle")

    nearest_ball_point, nearest_poly_point = shapely.ops.nearest_points(ball.shape, paddle.shape)
    paddle_hit_x, paddle_hit_y = list(nearest_poly_point.coords)[0]
    logger.debug(f"Ball hit paddle at {paddle_hit_y}")

    paddle_min_x, paddle_min_y, paddle_max_x, paddle_max_y = paddle.shape.bounds
    paddle_half_lenth = (paddle_max_y - paddle_min_y) / 2.0
    _, paddle_mid_y = list(paddle.shape.centroid.coords)[0]
    hit_distance_from_center = math.fabs(paddle_hit_y - paddle_mid_y)
    normalized_hit_distance_from_center = sorted([0, hit_distance_from_center / paddle_half_lenth, 1])[1]
    rebound_angle = MAX_ANGLE * normalized_hit_distance_from_center

    # try to avoid horizontal back and forth
    # if rebound_angle.magnitude < 0.5:
    #     rebound_angle = 0.5 * ureg.angular_degree

    rebound_vel_x = ball.vnorm * math.cos(rebound_angle.to_base_units().magnitude)
    rebound_vel_x = rebound_vel_x if ball.velocity[0] < 0 else -rebound_vel_x

    rebound_vel_y = ball.vnorm * math.sin(rebound_angle.to_base_units().magnitude)
    rebound_vel_y = -rebound_vel_y if paddle_hit_y < paddle_mid_y else rebound_vel_y
    ball.velocity = (rebound_vel_x, rebound_vel_y)


class CollisionStrategyByFlavor:
    def __init__(self, primary_ball_callable_provider: DelegatedCallable):
        self.primary_ball_callable_provider = primary_ball_callable_provider

    def provide_callable(self, ball_flavor: BallFlavor) -> Callable:
        if ball_flavor is BallFlavor.PRIMARY:
            return self.primary_ball_callable_provider
        else:
            return lambda *args: None


class BallPaddleCollider(ActorPairCollidor):
    """
    Models a classic pong paddle whereby if the ball hits the upper part of the paddle is will rebound upward and
    if it hits the bottom part of the paddle it will rebound downward
    """

    def __init__(self, classic_paddle_collision_factory: CollisionStrategyByFlavor):
        self.classic_paddle_collision_factory = classic_paddle_collision_factory

    def update_pair_state(self, ball: Ball, paddle: Paddle):
        if not isinstance(ball, Ball) or not isinstance(paddle, Paddle):
            return
        collision_strategy_callable = self.classic_paddle_collision_factory.provide_callable(ball.flavor)
        collision_strategy_callable(ball, paddle)
