import itertools
from abc import ABC, abstractmethod
from typing import List

import numpy
from shapely import affinity
from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

from config import property_configurator
from gameengine.gameactors import Actor, Ball, Paddle

"""
 Between every rendered frame, an object will move from its current position to the position defined by the 
 end of its velocity vector.  If the velocity is more than one pixel, then we will be 'teleporting' pixels between
 renders.    The purpose of this module is to handle the physics during this time so at the time of a render the 
 accurate screen representation of the result of all the interactions will be shown
"""

# this is the maximum number of pixels any game object can move between consecutive frames
PHYSICS_FRAME_RATE = property_configurator.game_engine_config.max_speed


def calculate_potential_collision(actor1: Actor, actor2: Actor) -> int:
    """
    Two actors may collide if their projected paths cross
    :param actor1:
    :param actor2:
    :return: if no collision possible: 0, otherwise 1
    """
    if not (actor1.is_collision_enabled() and actor2.is_collision_enabled()
        or (actor1 is actor2)
        or (numpy.linalg.norm(actor1.velocity) == 0 and numpy.linalg.norm(actor2.velocity) == 0)):
    # can't collide unless both have collision enabled, can't collide with self
        return 0

    actor1_line_string = LineString(
        [actor1.shape.centroid, (actor1.centroid[0] + actor1.velocity[0], actor1.centroid[1] + actor1.velocity[1])])

    actor2_line_string = LineString(
        [actor2.shape.centroid, (actor2.centroid[0] + actor2.velocity[0], actor2.centroid[1] + actor2.velocity[1])])

    for frame_index in range(PHYSICS_FRAME_RATE):
        actor_1_x, actor_1_y = actor1_line_string.interpolate(frame_index, normalized=True).coords[0]
        actor_2_x, actor_2_y = actor2_line_string.interpolate(frame_index, normalized=True).coords[0]

        actor_1_delta_x = actor_1_x - actor1.shape.centroid.x
        actor_1_delta_y = actor_1_y - actor1.shape.centroid.y
        actor_1_teleported_shape: BaseGeometry = affinity.translate(actor1.shape, actor_1_delta_x, actor_1_delta_y)

        actor_2_delta_x = actor_2_x - actor2.shape.centroid.x
        actor_2_delta_y = actor_2_y - actor2.shape.centroid.y
        actor_2_teleported_shape: BaseGeometry = affinity.translate(actor2.shape, actor_2_delta_x, actor_2_delta_y)

        if actor_1_teleported_shape.intersects(actor_2_teleported_shape):
            return 1
    return 0


class ActorPairCollidor(ABC):
    @abstractmethod
    def update_pair_state(self, actor1: Actor, actor2: Actor):
        pass


class NoOpPairCollision(ActorPairCollidor):
    def update_pair_state(self, actor1: Actor, actor2: Actor):
        pass


class CollisionPairHandlerFactory:
    def __init__(self, ball_to_ball_handler: ActorPairCollidor,
                 ball_to_barrier_handler: ActorPairCollidor,
                 ball_to_paddle_handler: ActorPairCollidor):
        self.ball_to_ball_handler = ball_to_ball_handler
        self.ball_to_barrier_handler = ball_to_barrier_handler
        self.ball_to_paddle_handler = ball_to_paddle_handler

    def get_collision_handler(self, actor1: Ball, actor2: Actor) -> ActorPairCollidor:
        if not isinstance(actor1, Ball):
            return NoOpPairCollision()

        if isinstance(actor2, Ball):
            handler = self.ball_to_ball_handler
        elif isinstance(actor2, Paddle):
            handler = self.ball_to_paddle_handler
        else:
            handler = self.ball_to_barrier_handler
        return handler


class GameCollisionEngine(ABC):
    @abstractmethod
    def update_state(self, actors: List[Actor]):
        """
        The game collision engine will be called upon between every frame render.  It's responsibility is
        to move the actors according to their velocities and detect collisions.  When collisions are detected,
        the game collision engine must update the state of the actors involved in the collision
        :param actors:  a list of actors
        :return: None
        """
        pass


class DefaultGameCollisionEngine(GameCollisionEngine):
    def __init__(self, collision_pair_handler_factory: CollisionPairHandlerFactory):
        self.collision_pair_handler_factory = collision_pair_handler_factory

    def update_state(self, actors: List[Actor]):
        # first lets see if there are any potential collisions
        possible_collision_pairs = itertools.combinations(actors, 2)
        any_possible_collision = any(
            map(lambda pair: calculate_potential_collision(pair[0], pair[1]), possible_collision_pairs))

        if not any_possible_collision:
            for actor in actors: actor.move_forward()
        else:
            balls, non_balls = [], []
            for actor in actors:
                (balls if isinstance(actor, Ball) else non_balls).append(actor)

            ball_to_other_pairs = itertools.product(balls, non_balls)
            ball_to_ball_pairs = itertools.combinations(balls, 2)
            for frame_index in range(PHYSICS_FRAME_RATE):
                for collision_pair in itertools.chain(ball_to_other_pairs, ball_to_ball_pairs):
                    collision_handler = self.collision_pair_handler_factory.get_collision_handler(*collision_pair)
                    collision_handler.update_pair_state(*collision_pair)
                for actor in actors: actor.move_forward(1.0 / PHYSICS_FRAME_RATE)
