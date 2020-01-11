import itertools
from abc import ABC, abstractmethod
from typing import List

import shapely
from shapely.geometry import LineString
from shapely import affinity
from shapely.geometry.base import BaseGeometry

from gameengine.gameactors import Actor



"""
 Between every rendered frame, an object will move from its current position to the position defined by the 
 end of its velocity vector.  If the velocity is more than one pixel, then we will be 'teleporting' pixels between
 renders.    The purpose of this module is to handle the physics during this time so at the time of a render the 
 accurate screen representation of the result of all the interactions will be shown
"""

physics_frame_rate = 10

def calculate_potential_collision(actor1: Actor, actor2: Actor) -> int:
    """
    Two actors may collide if their projected paths cross
    :param actor1:
    :param actor2:
    :return: if no collision possible: 0, otherwise 1
    """
    if not (actor1.is_collision_enabled() and actor2.is_collision_enabled()):
        # can't collide unless both have collision enabled
        return 0

    if actor1 is actor2:
        # can't collide with yourself
        return 0

    actor1_line_string = LineString([actor1.shape.centroid, (actor1.velocity.vel_x, actor1.velocity.vel_y)])
    actor2_line_string = LineString([actor2.shape.centroid, (actor2.velocity.vel_x, actor2.velocity.vel_y)])

    for frame_index in range(physics_frame_rate):
        actor_1_x, actor_1_y = actor1_line_string.interpolate(frame_index, normalized=True)
        actor_2_x, actor_2_y = actor2_line_string.interpolate(frame_index, normalized=True)

        actor_1_delta_x = actor_1_x - actor1.shape.centroid.x
        actor_1_delta_y = actor_1_y - actor1.shape.centroid.y
        actor_1_teleported_shape: BaseGeometry = affinity.translate(actor1.shape, actor_1_delta_x, actor_1_delta_y)

        actor_2_delta_x = actor_2_x - actor2.shape.centroid.x
        actor_2_delta_y = actor_2_y - actor2.shape.centroid.y
        actor_2_teleported_shape: BaseGeometry = affinity.translate(actor2.shape, actor_2_delta_x, actor_2_delta_y)

        if actor_1_teleported_shape.intersects(actor_2_teleported_shape):
            return 1
    return 0

class Collision_Engine:
    def update_state(self, actors : List[Actor]):
        # first lets see if there are any potential collisions
        possible_collision_pairs = itertools.product(actors, actors)
        any_possible_collision = any(map(calculate_potential_collision, *possible_collision_pairs))

        if not any_possible_collision:
            for actor in actors:
                actor.update_shape()
        else:




        for frame_index in range(physics_frame_rate):




