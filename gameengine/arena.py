import itertools
from typing import List

import shapely
from shapely import affinity
from shapely.geometry import Polygon

from gameengine.gameactors import StationaryActor, Paddle, Actor, Wall, Net


def calculate_collision_distance(actor1: Actor, actor2: Actor) -> float:
    if not actor1.is_collision_enabled() or not actor2.is_collision_enabled():
        return -1




class Arena:
    def __init__(self, arena_width: int, arena_height: int, line_thickness: int,
                 left_paddle: Paddle,
                 right_paddle: Paddle,
                 actors: List[Actor]):
        """

        :param arena_width:    width in pixels
        :param arena_height:   height in pixels
        :param line_thickness: in pixels
        :param left_paddle:    the paddle for left hand side
        :param right_paddle:   the paddle for right hand side
        :param actors:         anything else, such as the primary ball, other balls, other shapes, etc
        """
        self.top_wall = Wall(StationaryPolygon(shapely.geometry.box(0, 0, arena_width, line_thickness),
                                           collision_enabled=True, rebound_enabled=False))
        self.bottom_wall = Wall(StationaryPolygon(
            shapely.geometry.box(0, arena_height - line_thickness, arena_width, arena_height), collision_enabled=True,
            rebound_enabled=False))

        self.center_net = Net(StationaryPolygon(
            affinity.translate(shapely.geometry.box(0, 0, 1, arena_height), xoff=arena_width / 2),
            collision_enabled=False, rebound_enabled=False))

        self.paddles = (left_paddle, right_paddle)
        self.actors = actors
        self.all_actors = [self.top_wall, self.bottom_wall, self.center_net, self.paddles[0], self.paddles[1]]
        self.all_actors.extend(self.actors)

    def update_state(self):
        for reboundable_actor in [actor for actor in self.actors if actor.is_reboundable()]:
            pass

    def find_collision_pairs(self):
        all_entities = [self.top_bound, self.bottom_bound, self.center_net, self.paddles[0], self.paddles[1]]
        all_entities.extend(self.actors)





