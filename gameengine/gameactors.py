from abc import ABC, abstractmethod
from collections import namedtuple
from enum import Enum
from typing import Tuple

import numpy
from shapely import affinity
from shapely.geometry import Polygon, LineString
from shapely.geometry.base import BaseGeometry

from config.property_configurator import game_engine_config

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
    @abstractmethod
    def speed_bound(self) -> Tuple[int, int]:
        """
        :return: The (miniumum, maximum) pixels the actor can move between consecutive frames
        """
        pass

    def throttle_velocity(self) -> None:
        """
        The velocity of the object will be throttled, if necessary, to the maximum allowed
        :return:  None
        """
        if not isinstance(self, StationaryActor):
            v_norm = numpy.linalg.norm(self.velocity)
            if v_norm == 0:
                return

            min_vel, max_vel = self.speed_bound
            if v_norm > max_vel:
                self.velocity = (max_vel / v_norm) * self.velocity
            elif v_norm < min_vel:
                self.velocity = (min_vel / v_norm) * self.velocity


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
    def velocity(self, updated_velocity_array: Tuple[float, float]):
        """
        :param updated_velocity_array:  any structure having a first and second indexable element
        :return: None
        """
        self._velocity = Velocity(updated_velocity_array[0], updated_velocity_array[1])
        self.throttle_velocity()

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
        self.translate(x_offset, y_offset)

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
        self.translate(-x_offset, -y_offset)

    def translate(self, x_offset: float, y_offset: float) -> None:
        """
        Shape will be translated by the offset amount
        :param x_offset: offset in x direction
        :param y_offset: offset in y direction
        :return: None
        """
        self._shape = affinity.translate(self._shape, x_offset, y_offset)

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

    @property
    def speed_bound(self) -> Tuple[int, int]:
        return (0,0)

class Wall(StationaryActor):
    def __init__(self, name: str, polygon: Polygon, collision_enabled: bool = True):
        super().__init__(name, polygon, collision_enabled, rebound_enabled=False)


class Net(StationaryActor):
    def __init__(self, name: str, polygon: Polygon):
        super().__init__(name, polygon, collision_enabled=False, rebound_enabled=False)


class Paddle(Actor):
    def __init__(self, name: str, polygon: Polygon, velocity: Velocity):
        super().__init__(name, polygon, velocity, collision_enabled=True, rebound_enabled=False)
        self._max_paddle_speed = game_engine_config.max_paddle_speed
        self._min_paddle_speed = game_engine_config.min_paddle_speed
        if numpy.linalg.norm(self.velocity) > 0:
            self.throttle_velocity()

    @property
    def speed_bound(self) -> Tuple[int, int]:
        return (self._min_paddle_speed, self._max_paddle_speed)

class BallColor(Enum):
    WHITE = 1
    RED = 2
    GREEN = 3


class Ball(Actor):
    def __init__(self, name: str, polygon: Polygon, velocity: Velocity, color: BallColor):
        """
        :param name:      an identifier for the ball
        :param polygon:   shape of the ball
        :param velocity:  initial speed of the ball
        :param color:     the ball color.  Different color balls will have different collision models
        """
        super().__init__(name, polygon, velocity, collision_enabled=True, rebound_enabled=True)
        self._max_ball_speed = game_engine_config.max_ball_speed
        self._min_ball_speed = game_engine_config.min_ball_speed
        self.color = color
        if numpy.linalg.norm(self.velocity) > 0:
            self.throttle_velocity()

    @property
    def speed_bound(self) -> Tuple[int, int]:
        return self._min_ball_speed, self._max_ball_speed







