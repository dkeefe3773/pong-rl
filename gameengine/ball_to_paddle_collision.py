import math

import numpy
import shapely
from shapely import ops

from config import logging_configurator
from gameengine.collision_engine import ActorPairCollision
from gameengine.gameactors import Actor, Ball, Paddle


logger = logging_configurator.get_logger(__name__)

class ClassicPongCollision(ActorPairCollision):
    def update_pair_state(self, ball: Actor, paddle: Actor):
        if not isinstance(ball, Ball) or not isinstance(paddle, Paddle):
            return

        actors_intersect = ball.shape.intersects(paddle.shape)
        if not actors_intersect:
            return

        logger.debug(f"Begin classic pong paddle ball collission modeling for {ball.name} and {paddle.name}")
        # lets make ball back up so it is not intersecting anymore.  We will try to back up one pixel at a time
        ball_backup_distance = 1. / numpy.linalg.norm(ball.velocity)
        while actors_intersect:
            logger.debug("Moving ball backwards one pixel at a time")
            ball.move_backward(ball_backup_distance)
            actors_intersect = ball.shape.intersects(paddle.shape)
        logger.debug("Ball no longer intsersects paddle")

        nearest_ball_point, nearest_poly_point = shapely.ops.nearest_points(ball.shape, paddle.shape)
        paddle_hit_x, paddle_hit_y = nearest_poly_point

        paddle_min_x, paddle_min_y, paddle_max_x, paddle_max_y = paddle.shape.bounds
        paddle_half_lenth = (paddle_max_y - paddle_min_y) / 2.0
        _, paddle_mid_y = paddle.shape.centroid
        hit_distance_from_center = math.fabs(paddle_hit_y - paddle_mid_y)
        normalized_hit_distance_from_center = sorted([0, hit_distance_from_center / paddle_half_lenth, 1])[1]




