from abc import abstractmethod, ABC
from collections import namedtuple
from typing import Tuple

from shapely.geometry import Polygon, LineString
from shapely.geometry.base import BaseGeometry
from shapely import affinity

Velocity = namedtuple('Velocity', ['vel_x', 'vel_y'])

class Actor(ABC):
    @abstractmethod
    @property
    def shape(self) -> BaseGeometry:
        pass

    @abstractmethod
    @property
    def velocity(self) -> Velocity:
        pass

    @abstractmethod
    @velocity.setter
    def velocity(self, updated_velocity: Velocity):
        pass

    @abstractmethod
    def apply_velocity(self):
        pass

    @abstractmethod
    def is_collision_enabled(self) -> bool:
        """
        :return:  True if collision detection is valid for this object
        """
        pass

    @abstractmethod
    def is_reboundable(self) -> bool:
        """
        :return:  True if this actor rebounds upon collision
        """

class MovingPolygon(Actor):
    """
    Represents a polygon with a velocity
    """
    def __init__(self, polygon: Polygon, velocity: Velocity, collision_enabled: bool = True, rebound_enabled: bool = True):
        self._shape = polygon
        self._velocity = velocity
        self.collision_enabled = collision_enabled
        self.rebound_enabled = rebound_enabled

    @property
    def shape(self) -> Polygon:
        return self._shape

    @property
    def velocity(self) -> Velocity:
        return self._velocity

    @velocity.setter
    def velocity(self, updated_velocity: Velocity):
        self._velocity = updated_velocity

    def apply_velocity(self, relative_distance=1):
        x_offset = 0
        y_offset = 0
        if relative_distance is None or relative_distance >= 1:
            x_offset = self._velocity.vel_x
            y_offset = self._velocity.vel_y
            self._shape = affinity.translate(self._shape, xoff=self._velocity.vel_x, yoff=self._velocity.vel_y)
        else:
            line_segment = LineString([self._shape.centroid, (self._velocity.vel_x, self._velocity.vel_y)])
            interp_point = line_segment.interpolate(relative_distance, normalized=True)
            x_offset = x_interp - self._shape.centroid.x
            y_offset = y_interp - self._shape.centroid.y
        self._shape = affinity.translate(self._shape, x_offset, y_offset)


    def is_collision_enabled(self) -> bool:
        return self.collision_enabled

    def is_reboundable(self) -> bool:
        return self.rebound_enabled

class StationaryPolygon(Actor):
    """
    Represents a polygon with a fixed zero velocity
    """
    def __init__(self, polygon: Polygon, collision_enabled: bool = True, rebound_enabled: bool = True):
        self._shape = polygon
        self._velocity = Velocity(0,0)
        self.collision_enabled = collision_enabled
        self.rebound_enabled = rebound_enabled

    @property
    def shape(self) -> Polygon:
        return self._shape

    @property
    def velocity(self) -> Velocity:
        return self._velocity

    @velocity.setter
    def velocity(self, updated_velocity: Velocity):
        pass

    def apply_velocity(self):
        pass

    def is_collision_enabled(self) -> bool:
        return self.collision_enabled

    def is_reboundable(self) -> bool:
        return self.rebound_enabled


class Paddle:
    def __init__(self, moving_polyon: MovingPolygon):
        self.moving_polygon = moving_polyon

class Ball:
    def __init__(self, moving_polyon: MovingPolygon):
        self.moving_polygon = moving_polyon
