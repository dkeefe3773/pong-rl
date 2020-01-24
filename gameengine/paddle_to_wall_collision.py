import math
from typing import Callable

import numpy
import shapely
from dependency_injector.providers import DelegatedCallable
from shapely import ops

from config import logging_configurator, property_configurator
from gameengine.collision_engine import ActorPairCollidor
from gameengine.gameactors import Ball, Paddle, BallFlavor, Wall

logger = logging_configurator.get_logger(__name__)

def update_paddle(paddle: Paddle, wall: Wall):
    actors_intersect = paddle.shape.intersects(wall.shape)
    if not actors_intersect:
        return

    # lets make the paddle up so it is not intersecting anymore.  We will try to back up one pixel at a time
    paddle_backup_distance = 1. / paddle.vnorm
    while actors_intersect:
        paddle.move_backward(paddle_backup_distance)
        actors_intersect = paddle.shape.intersects(wall.shape)

    # now set the paddle velocity to zero
    paddle.velocity = (0,0)

class PaddleWallCollider(ActorPairCollidor):
    """
    Models a paddle running into a wall
    """
    def update_pair_state(self, paddle: Paddle, wall: Wall):
        if not isinstance(paddle, Paddle) or not isinstance(wall, Wall):
            return
        return update_paddle(paddle, wall)
