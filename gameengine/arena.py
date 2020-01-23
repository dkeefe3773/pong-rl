import math
import random
from typing import List

import numpy
import shapely
from shapely import affinity
from shapely.geometry import Polygon

from config import property_configurator, logging_configurator
from config.property_configurator import game_arena_config
from gameengine.gameactors import Actor, Wall, Net, Paddle, Velocity, Ball, BallFlavor, BackLine
from proto_gen.gamemaster_pb2 import PaddleType
from utils.measures import ureg

PADDLE_OFFSET = property_configurator.game_arena_config.paddle_offset
PADDLE_HEIGHT = property_configurator.game_arena_config.paddle_height
PADDLE_WIDTH = property_configurator.game_arena_config.paddle_width

WHITE_BALL_RADIUS = property_configurator.game_arena_config.white_ball_radius
MAX_BALL_START_ANGLE = property_configurator.game_arena_config.max_ball_starting_angle
STARTING_BALL_SPEED = property_configurator.game_arena_config.starting_ball_speed

logger = logging_configurator.get_logger(__name__)


class Arena:
    def __init__(self, other_actors: List[Actor] = None):
        """
        :param actors:         any other shapes besides the white ball, paddles, and arena bounds
        """
        self.arena_width = game_arena_config.arena_width
        self.arena_height = game_arena_config.arena_height
        self.arena_center = numpy.array([int(self.arena_width // 2), int(self.arena_height // 2)])

        self.top_wall = Wall(name="top_wall",
                             polygon=shapely.geometry.box(0, 0, self.arena_width, game_arena_config.wall_thickness),
                             collision_enabled=True)

        self.bottom_wall = Wall(name="bottom_wall",
                                polygon=shapely.geometry.box(0, self.arena_height - game_arena_config.wall_thickness,
                                                             self.arena_width, self.arena_height),
                                collision_enabled=True)

        self.center_net = Net(name="net",
                              polygon=affinity.translate(shapely.geometry.box(0, 0, 1, self.arena_height),
                                                         xoff=self.arena_width // 2))

        self.left_back_line = BackLine(name="left back line",
                                       polygon=affinity.translate(shapely.geometry.box(0, 0, 1, self.arena_height),
                                                                  xoff=PADDLE_OFFSET + PADDLE_WIDTH // 2))

        self.right_back_line = BackLine(name="right back line",
                                        polygon=affinity.translate(shapely.geometry.box(0, 0, 1, self.arena_height),
                                                                   xoff=self.arena_width - PADDLE_OFFSET - PADDLE_WIDTH // 2))

        self.make_primary_ball()
        self.make_paddles()

        # the specified order will also be the rendering order.  Later actors will overlay on top of earlier actors
        self.actors = [self.center_net, self.left_back_line, self.right_back_line,
                       self.primary_ball, self.paddles[0], self.paddles[1], self.top_wall, self.bottom_wall]
        if other_actors:
            self.actors.extend(other_actors)
        self.reset_starting_positions()

    def reset_starting_positions(self):
        """
        Will move paddles and balls back to starting positions.
        Paddle velocities will be set to zero and ball velocities will be randomized
        :return: None
        """
        for paddle in filter(lambda actor: isinstance(actor, Paddle), self.actors):
            offset_to_center = paddle.centroid - self.arena_center
            paddle.translate(0, -offset_to_center[1])
            paddle.velocity = (0,0)

        for ball in filter(lambda actor: isinstance(actor, Ball), self.actors):
            offset_to_center = ball.centroid - self.arena_center
            ball.translate(-offset_to_center[0], -offset_to_center[1])
            max_angle_degrees = MAX_BALL_START_ANGLE.to(ureg.angular_degrees).magnitude
            random_angle = random.randint(0, math.fabs(max_angle_degrees)) * ureg.angular_degree
            vel_x = STARTING_BALL_SPEED * math.cos(random_angle.to_base_units()) * random.choice([-1, 1])
            vel_y = STARTING_BALL_SPEED * math.sin(random_angle.to_base_units()) * random.choice([-1, 1])
            ball.velocity = (vel_x, vel_y)

    def make_primary_ball(self):
        ball_shape = shapely.geometry.Point(self.arena_width / 2, self.arena_height / 2).buffer(WHITE_BALL_RADIUS)
        self.primary_ball = Ball('primary_ball', ball_shape, Velocity(0, 0), BallFlavor.PRIMARY)

    def make_paddles(self):
        left_paddle_poly = shapely.geometry.box(PADDLE_OFFSET,
                                                int((self.arena_height / 2.) - PADDLE_HEIGHT / 2),
                                                PADDLE_OFFSET + PADDLE_WIDTH,
                                                int((self.arena_height / 2.0) + PADDLE_HEIGHT / 2))
        left_paddle = Paddle("left_paddle", left_paddle_poly, Velocity(0, 0), PaddleType.LEFT)

        right_paddle_poly = shapely.geometry.box(self.arena_width - PADDLE_OFFSET - PADDLE_WIDTH,
                                                 int((self.arena_height / 2.) - PADDLE_HEIGHT / 2),
                                                 self.arena_width - PADDLE_OFFSET,
                                                 int((self.arena_height / 2.0) + PADDLE_HEIGHT / 2))
        right_paddle = Paddle("right_paddle", right_paddle_poly, Velocity(0, 0), PaddleType.RIGHT)
        self.paddles = (left_paddle, right_paddle)

    def find_collision_pairs(self):
        all_entities = [self.top_bound, self.bottom_bound, self.center_net, self.paddles[0], self.paddles[1]]
        all_entities.extend(self.actors)
