import itertools
import math
from operator import itemgetter

import numpy
from shapely.geometry import Polygon, LineString

from config import logging_configurator
from gameengine.collision_engine import ActorPairCollidor
from gameengine.gameactors import Actor, Ball

logger = logging_configurator.get_logger(__name__)

to_euclidean_transform = numpy.array([[1, 0], [0, -1]])  # transforms canvas coordinates to euclidean standard
to_canvas_transform = numpy.linalg.inv(to_euclidean_transform) # transforms standard coordinates to canvas


def line_segment_rebound(ball: Ball, line_segment: LineString):
    """
    We are assuming elastic collision where angle of incidence equals angle of reflection.
    :param ball:                 the ball
    :param line_segment:         a line segment
    :return: the velocity for the ball after rebounding
    """
    # we can simply take the dot product of the velocity vector of the ball to the normal of the line to
    # calculate the new velocity.
    # Vnew = Vold - 2 <v|n> n_hat
    # Note, the normal vector can just be -sin(phi) i_hat + cos(phi) j_hat, where phi is the angle from horizontal
    # between [-90, 90].  Well, this is true in euclidean standard basis.  In the canvas basis (where y is flipped)
    # the normal vector is calculated differently.  I keep getting sign errors so rather than figuring it out,
    # lets just transform the objects and velocities of the problem into standard euclidean for the calculation then
    # we can inverse transform at the end.
    vel_canvas = ball.velocity
    vel_standard = to_euclidean_transform.dot(vel_canvas)
    segment_coords_canvas_matrix = numpy.array(list(line_segment.coords)).transpose()  # columns are the coordinates
    segment_coords_standard_matrix = to_euclidean_transform.dot(segment_coords_canvas_matrix)
    coords_standard_list = [tuple(segment_coords_standard_matrix[:, 0]), tuple(segment_coords_standard_matrix[:, 1])]
    coords_standard_list.sort(key=itemgetter(0))  # sort points by the x-coord
    delta_x = coords_standard_list[1][0] - coords_standard_list[0][0]
    phi = math.acos(delta_x / line_segment.length)  # this is the angle from horizontal

    # if the second point is below us (in standard coords) then flip sign of angle
    if coords_standard_list[1][1] < coords_standard_list[0][1]:
        phi *= -1
    normal = numpy.array([-1 * math.sin(phi), math.cos(phi)])

    rebound_vel_standard = vel_standard - 2 * numpy.dot(vel_standard, normal) * normal
    rebound_vel_canvas = to_canvas_transform.dot(rebound_vel_standard)
    return rebound_vel_canvas


class IncidentAngleRebounder(ActorPairCollidor):
    def update_pair_state(self, ball: Actor, barrier: Actor):
        if not isinstance(ball, Ball) or barrier.is_reboundable() \
                or not isinstance(barrier.shape, Polygon) \
                or not barrier.is_collision_enabled():
            return

        actors_intersect = ball.shape.intersects(barrier.shape)
        if not actors_intersect:
            return

        logger.debug(f"Begin incident angle collision modeling for {ball.name} and {barrier.name}")
        # lets make ball back up so it is not intersecting anymore.  We will try to back up one pixel at a time
        ball_backup_distance = 1. / numpy.linalg.norm(ball.velocity)
        while actors_intersect:
            logger.debug("Moving ball backwards one pixel at a time")
            ball.move_backward(ball_backup_distance)
            actors_intersect = ball.shape.intersects(barrier.shape)
        logger.debug("Ball no longer intsersects barrier")

        # ok, our goal is to find the line segment of the polygon that we are closest too.  We will then bounce
        # off this line segment
        tee1, tee2 = itertools.tee(barrier.shape.exterior.coords)
        next(tee2)
        coord_sequence = zip(tee1, tee2)
        line_segements = [LineString(pair) for pair in coord_sequence]
        distances_to_segments = list(map(lambda segment: ball.shape.distance(segment), line_segements))
        closest_segment_index = min(enumerate(distances_to_segments), key=itemgetter(1))[0]
        closest_line_segment = line_segements[closest_segment_index]

        logger.debug(f"Ball velocity before line segment rebound {ball.velocity}")
        ball.velocity = line_segment_rebound(ball, closest_line_segment)
        logger.debug(f"Ball velocity after line segment rebound {ball.velocity}")

