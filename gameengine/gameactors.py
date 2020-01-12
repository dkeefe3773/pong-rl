from abc import ABC
from collections import namedtuple

import numpy
from shapely import affinity
from shapely.geometry import Polygon, LineString
from shapely.geometry.base import BaseGeometry

Velocity = namedtuple('Velocity', ['vel_x', 'vel_y'])


class Actor(ABC):
    def __init__(self, name: str, shape: BaseGeometry, velocity: Velocity, collision_enabled: bool,
                 rebound_enabled: bool):
        self.name = name
        self._shape = shape
        self._velocity = velocity
        self._collision_enabled = collision_enabled
        self._rebound_enabled = rebound_enabled

    @property
    def shape(self) -> BaseGeometry:
        return self._shape

    @property
    def velocity(self):
        """
        :return:  numpy version of the velocity
        """
        return numpy.array([self._velocity.vel_x, self._velocity.vel_y])

    @velocity.setter
    def velocity(self, updated_velocity_array: Velocity):
        """
        :param updated_velocity_array:  any structure having a first and second indexable element
        :return: None
        """
        self._velocity = Velocity(updated_velocity_array[0], updated_velocity_array[1])

    @property
    def centroid(self):
        """
        :return:  The centroid of the shape as a numpy array
        """
        return numpy.array([self._shape.centroid.x, self._shape.centroid.y])

    def move_forward(self, relative_distance=1):
        """
        Moves object forward along its velocity vector
        :param relative_distance: The distance to move the object along its velocity vector, relative to the length of the velocity vector
               If None or not provided, will move the full length of the velocity vector
        :return: None, mutates in place
        """
        if relative_distance is None or relative_distance >= 1:
            x_offset = self._velocity.vel_x
            y_offset = self._velocity.vel_y
        else:
            line_segment = LineString([self._shape.centroid, (self._velocity.vel_x, self._velocity.vel_y)])
            interp_point = line_segment.interpolate(relative_distance, normalized=True)
            x_offset = interp_point.x - self._shape.centroid.x
            y_offset = interp_point.y - self._shape.centroid.y
        self._shape = affinity.translate(self._shape, x_offset, y_offset)

    def move_backward(self, relative_distance=1):
        """
        Moves object backwards along its velocity vector
        :param relative_distance: The distance to move the object along its negative velocity vector, relative to the length of the velocity vector
               If None or not provided, will move the full length of the velocity vector
        :return: None, mutates in place
        """
        if relative_distance is None or relative_distance >= 1:
            x_offset = self._velocity.vel_x
            y_offset = self._velocity.vel_y
        else:
            line_segment = LineString([self._shape.centroid, (self._velocity.vel_x, self._velocity.vel_y)])
            interp_point = line_segment.interpolate(relative_distance, normalized=True)
            x_offset = interp_point.x - self._shape.centroid.x
            y_offset = interp_point.y - self._shape.centroid.y
        self._shape = affinity.translate(self._shape, -x_offset, -y_offset)

    def is_collision_enabled(self) -> bool:
        """
        :return:  True if collision detection is valid for this object
        """
        return self._collision_enabled

    def is_reboundable(self) -> bool:
        """
        :return:  True if this actor rebounds upon collision
        """
        return self._rebound_enabled


class StationaryActor(Actor, ABC):
    """
    Represents an actor with a fixed zero velocity
    """

    def __init__(self, name: str, polygon: Polygon, collision_enabled: bool = True, rebound_enabled: bool = False):
        super().__init__(name, polygon, Velocity(0, 0), collision_enabled, rebound_enabled)

    @property
    def velocity(self) -> Velocity:
        return self._velocity

    @velocity.setter
    def velocity(self, updated_velocity: Velocity):
        pass

    def move_forward(self, relative_distance=1):
        pass

    def move_backward(self, relative_distance=1):
        pass


class Wall(StationaryActor):
    def __init__(self, name: str, polygon: Polygon, collision_enabled: bool = True):
        super().__init__(name, polygon, collision_enabled, rebound_enabled=False)


class Net(StationaryActor):
    def __init__(self, name: str, polygon: Polygon):
        super().__init__(name, polygon, collision_enabled=False, rebound_enabled=False)


class Paddle(Actor):
    def __init__(self, name: str, polygon: Polygon, velocity: Velocity):
        super().__init__(name, polygon, velocity, collision_enabled=True, rebound_enabled=False)


class Ball(Actor):
    def __init__(self, name: str, polygon: Polygon, velocity: Velocity):
        super().__init__(name, polygon, velocity, collision_enabled=True, rebound_enabled=True)
