import itertools
from abc import ABC, abstractmethod
from typing import List, Callable

from shapely.geometry import box

from config import property_configurator
from gameengine.gameactors import Actor, Ball, Paddle, Wall

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
    :return: if no collision possible: false, otherwise true
    """
    if not actor1.is_collision_enabled() or \
            not actor2.is_collision_enabled() or \
            (actor1 is actor2) or \
            (actor1.vnorm == 0 and actor2.vnorm == 0):
        return False

    actor1_box = box(*actor1.shape.bounds).buffer(max(1, actor1.vnorm))
    actor2_box = box(*actor2.shape.bounds).buffer(max(1, actor2.vnorm))
    return actor1_box.intersects(actor2_box)


class ActorPairCollidor(ABC):
    @abstractmethod
    def update_pair_state(self, actor1: Actor, actor2: Actor):
        pass


class CollisionPairHandlerFactory:
    def __init__(self, ball_to_ball_handler: ActorPairCollidor,
                 ball_to_barrier_handler: ActorPairCollidor,
                 ball_to_paddle_handler: ActorPairCollidor,
                 paddle_to_wall_handler: ActorPairCollidor):
        self.actor_pair_type_to_handler = {
            (Ball, Ball): ball_to_ball_handler.update_pair_state,
            (Ball, Wall): ball_to_barrier_handler.update_pair_state,
            (Wall, Ball): lambda wall, ball: ball_to_barrier_handler.update_pair_state(ball, wall),
            (Ball, Paddle): ball_to_paddle_handler.update_pair_state,
            (Paddle, Ball): lambda paddle, ball: ball_to_paddle_handler.update_pair_state(ball, paddle),
            (Paddle, Wall): paddle_to_wall_handler.update_pair_state,
            (Wall, Paddle): lambda wall, paddle: paddle_to_wall_handler.update_pair_state(paddle, wall)
            }

    def get_collision_handler(self, actor1: Ball, actor2: Actor) -> Callable:
        return self.actor_pair_type_to_handler.get((actor1.__class__, actor2.__class__), lambda *args: None)


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


class AccurateGameCollisionEngine(GameCollisionEngine):
    """
    Provides an engine that covers for edge cases at the expense of frame rate.
    """

    def __init__(self, collision_pair_handler_factory: CollisionPairHandlerFactory):
        self.collision_pair_handler_factory = collision_pair_handler_factory

    def update_state(self, actors: List[Actor]):
        # first lets see if there are any potential collisions
        possible_collision_pairs = itertools.combinations(actors, 2)
        likely_collision_pairs = list(filter(lambda pair: calculate_potential_collision(pair[0], pair[1]),
                                             possible_collision_pairs))
        if not likely_collision_pairs:
            for actor in actors: actor.move_forward()
        else:
            collision_actor_set = set([actor for pair in likely_collision_pairs for actor in pair])
            actor_set = set(actors)
            non_collision_actors = actor_set.difference(collision_actor_set)
            for non_collision_actor in non_collision_actors: non_collision_actor.move_forward()

            for collision_pair in likely_collision_pairs:
                physics_rate = int(max(collision_pair[0].vnorm, collision_pair[1].vnorm))
                for physics_frame in range(physics_rate):
                    collision_handler = self.collision_pair_handler_factory.get_collision_handler(*collision_pair)
                    collision_handler(*collision_pair)
                    for collision_actor in collision_pair: collision_actor.move_forward(1.0 / physics_rate)


class FastGameCollisionEngine(GameCollisionEngine):
    """
    Provides a good enough engine in most cases.  If an object's velocity norm is greater than the width of
    an obstacle, the object will probably pass through.  Most arena configurations won't have this problem though.
    This is about 20-30 frames per second faster than AccurateGameCollisionEngine
    """

    def __init__(self, collision_pair_handler_factory: CollisionPairHandlerFactory):
        self.collision_pair_handler_factory = collision_pair_handler_factory

    def update_state(self, actors: List[Actor]):
        # first lets see if there are any potential collisions
        possible_collision_pairs = itertools.combinations(actors, 2)
        likely_collision_pairs = list(filter(lambda pair: calculate_potential_collision(pair[0], pair[1]),
                                             possible_collision_pairs))
        if not likely_collision_pairs:
            for actor in actors: actor.move_forward()
        else:
            collision_actor_set = set([actor for pair in likely_collision_pairs for actor in pair])
            actor_set = set(actors)
            non_collision_actors = actor_set.difference(collision_actor_set)
            for non_collision_actor in non_collision_actors: non_collision_actor.move_forward()

            for collision_pair in likely_collision_pairs:
                collision_handler = self.collision_pair_handler_factory.get_collision_handler(*collision_pair)
                collision_handler(*collision_pair)
            for collision_actor in collision_actor_set: collision_actor.move_forward(1.0)
