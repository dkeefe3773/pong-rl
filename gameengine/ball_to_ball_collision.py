from typing import Tuple, Any

import numpy

from config import logging_configurator
from gameengine.collision_engine import ActorPairCollidor
from gameengine.gameactors import Actor, Ball

logger = logging_configurator.get_logger(__name__)


def billiard_ball_rebound(ball1: Ball, ball2: Ball) -> Tuple[Any, Any]:
    """
    Derived from conservation of momentum assuming elastic collision (so KE also conserved)
    :param ball1:  first ball
    :param ball2:  second ball
    :return: tuple of velocities for their rebounds
    """
    mass_1 = ball1.shape.area
    mass_2 = ball2.shape.area
    total_mass = mass_1 + mass_2

    delta_v12 = ball1.velocity - ball2.velocity
    delta_v21 = delta_v12 * -1

    delta_x12 = ball1.shape.centroid - ball2.shape.centroid
    delta_x21 = delta_x12 * -1
    delta_x12_norm = numpy.linalg.norm(delta_x12)
    delta_x21_norm = numpy.linalg.norm(delta_x21)

    rebound_v1 = ball1.velocity - (
                2 * mass_2 / total_mass * numpy.dot(delta_v12, delta_x12) / delta_x12_norm ** 2) * delta_x12
    rebound_v2 = ball2.velocity - (
                2 * mass_1 / total_mass * numpy.dot(delta_v21, delta_x21) / delta_x21_norm ** 2) * delta_x21
    return rebound_v1, rebound_v2


class BilliardBallCollider(ActorPairCollidor):
    def update_pair_state(self, actor1: Actor, actor2: Actor):
        if not isinstance(actor1, Ball) or not isinstance(actor2, Ball):
            logger.error("BilliardBallModel called with non-ball actors.  Not updating state")
            return

        if not (actor1.is_reboundable() and actor2.is_reboundable()):
            logger.warn(
                "BilliardBallModel called with one or more actors that are not reboundable.  Not updating state")
            return

        actors_intersect = actor1.shape.intersects(actor2.shape)
        if not actors_intersect:
            return

        logger.debug(f"Begin billiard ball collision modeling for {actor1.name} and {actor2.name}")
        # lets make them back up so they are not intersecting anymore.  We will try to back up one pixel at a time
        actor1_backup_distance = 1. / numpy.linalg.norm(actor1.velocity)
        actor2_backup_distance = 1. / numpy.linalg.norm(actor2.velocity)
        while actors_intersect:
            logger.debug("Moving balls backwards one pixel at a time")
            actor1.move_backward(actor1_backup_distance)
            actor2.move_backward(actor2_backup_distance)
            actors_intersect = actor1.shape.intersects(actor2.shape)
        logger.debug("Balls no longer intsersect")

        logger.debug(f"Original velocities: {actor1.velocity} {actor2.velocity}")
        rebound_v1, rebound_v2 = billiard_ball_rebound(actor1, actor2)
        actor1.velocity = rebound_v1
        actor2.velocity = rebound_v2
        logger.debug(f"Updated velocities: {actor1.velocity} {actor2.velocity}")
