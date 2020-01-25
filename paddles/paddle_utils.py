from typing import Tuple, Optional, List

import numpy
from PIL import Image
from shapely import affinity
from shapely.geometry import Polygon

from gameengine.gameactors import Velocity
from proto_gen.gamemaster_pb2 import ImageFrame, PaddleType, GameState, Actor, ScoreCard, ActorType


def color_integer_to_rgb(color_integer: int) -> Tuple[int, int, int, int]:
    """
    Converts a color integer representing 32 bit depth into tuple of (alpha, red, blue, green)
    :param color_integer:
    :return: tuple of (a, r, b, g)
    """
    blue = color_integer & 255
    green = (color_integer >> 8) & 255
    red = (color_integer >> 16) & 255
    alpha = (color_integer >> 24) & 255
    return alpha, red, green, blue


def image_frame_to_array(image_frame: ImageFrame) -> numpy.ndarray:
    """
    :param image_frame:  a frame from the pygame server
    :return: a numpy array representation
    """
    flat_array: numpy.ndarray = numpy.frombuffer(image_frame.image, dtype=numpy.uint32)
    return numpy.reshape(flat_array, (image_frame.num_rows, image_frame.num_cols))


def show_image_from_array(array: numpy.ndarray):
    """
    This will convert the array to an image and then show the image in a frame.  Nice as a sanity check
    :param array:  a numpy array holding 32bit integer pixel values
    :return:  None
    """
    image = Image.fromarray(array)
    image.show()


def convert_bitdepth32_to_greyscale(array: numpy.ndarray, preserve_alpha: bool = False):
    """
    Converts a numpy array that represents an image having pixels as 32 bit color
    :param array: the numpy array representing the image
    :param preserve_alpha: if true, the grey scale will have an alpha channel as well, if available on the original array
    :return:  the converted image as numpy array having shape: [row, col, 1] -> for no alpha and [row,col,2] with alpha
    """
    grey_image = Image.fromarray(array).convert('LA') if preserve_alpha else Image.fromarray(array).convert('L')
    return numpy.array(grey_image)


def convert_bitdepth32_to_rgb(array: numpy.ndarray, preserve_alpha: bool = False):
    """
    Converts a numpy array that represents an image having pixels as 32 bit color
    :param array: the numpy array representing the image
    :param preserve_alpha: if true, the rgb will have an alpha channel as well, if available on the original array
    :return: the converted image as numpy array having shape: [row, col, 3] -> for no alpha and [row,col,4] with alpha
    """
    rgb_image = Image.fromarray(array).convert('RGBA') if preserve_alpha else Image.fromarray(array).convert('RGB')
    return numpy.array(rgb_image)


class ActorSummary:
    def __init__(self, poly: Polygon, vel: Velocity):
        self.shape = poly
        self.vel = vel

def actor_to_summary(actor: Actor, transform: List[int]) -> ActorSummary:
    poly = Polygon([(coord.x, coord.y) for coord in actor.coords])
    vel = [actor.velocity.x, actor.velocity.y]
    if transform:
        poly = affinity.affine_transform(poly, transform)
        vel[0] *= -1
    return ActorSummary(poly, Velocity(*vel))


class GameStateWrapper():
    """
    A helper class to manage a game state.  Game state actors will be provided as shapely polygons.  Mirror
    imaging will be done as appropriate on the image and the actors.
    """

    def __init__(self, paddle_type: PaddleType, mirror_reflect_arena: bool = False, preserve_alpha: bool = False):
        """
        :param paddle_type:         left or right
        :param mirror_reflect_arena: if you are assigned a right paddle but have an algorithm that works on the left,
        or vice-versa, set this property to true.  The image array will be flipped around the center column
        and the vel_x component sign will be flipped
        :param preserve_alpha: if true, rgb and/or grey scale arrays will preserve the alpha channel
        """
        self.paddle_type = paddle_type
        self.mirror_reflect_arena = mirror_reflect_arena
        self.preserve_alpha = preserve_alpha
        self._game_state: Optional[GameState] = None
        self._image_color32_array: Optional[numpy.ndarray] = None
        self._image_grey_array: Optional[numpy.ndarray] = None
        self._image_rgb_array: Optional[numpy.ndarray] = None
        self._primary_ball: Optional[ActorSummary] = None
        self._my_paddle: Optional[ActorSummary] = None
        self._opponent_paddle: Optional[ActorSummary] = None
        self._my_scorecard: Optional[ScoreCard] = None
        self._oppenent_scorecard: Optional[ScoreCard] = None

        # if mirror image is set to true, this provides the affine transform to convert all actors to mirror image
        self.transform: List[int] = []

    @property
    def game_state(self) -> GameState:
        """
        :return:  The unadulterated game state object
        """
        return self._game_state

    @game_state.setter
    def game_state(self, game_state: GameState):
        self._game_state = game_state
        self._primary_ball = None
        self._my_paddle = None
        self._oppenent_paddle = None
        self._my_scorecard = None
        self._oppenent_scorecard = None

        self._image_color32_array = image_frame_to_array(self._game_state.arena_frame)

        if self.mirror_reflect_arena:
            self._image_color32_array = numpy.fliplr(self._image_color32_array)
            if not self.transform:
                # [-1 0   xoffset]
                # [0 1    yoffset]
                # This transforms basis so x-axis is flipped and then slides the origin back the full width of the frame
                # to provide a mirror image
                self.transform.extend([-1, 0, 0, 1, self._image_color32_array.shape[1], 0])

    @property
    def image_color32_array(self) -> numpy.ndarray:
        """
        :return:  the arena frame where rgba pixels are encoded as 32 bit integers
        """
        return self._image_color32_array

    @property
    def image_grey_array(self) -> numpy.ndarray:
        """
        :return: the arena frame as greyscale array
        """
        if self._image_grey_array is None:
            self._image_grey_array = convert_bitdepth32_to_greyscale(self._image_color32_array, self.preserve_alpha)
        return self._image_grey_array

    @property
    def image_rgb_array(self) -> numpy.ndarray:
        """
        :return: the arena frame as greyscale array
        """
        if self._image_rgb_array is None:
            self._image_rgb_array = convert_bitdepth32_to_rgb(self._image_color32_array, self.preserve_alpha)
        return self._image_rgb_array

    @property
    def primary_ball(self) -> ActorSummary:
        if self._primary_ball is None:
            primary_ball_actor: Actor = next(
                filter(lambda actor: actor.actor_type is ActorType.PRIMARY_BALL, self._game_state.actors), None)
            if primary_ball_actor:
                self._primary_ball = actor_to_summary(primary_ball_actor, self.transform)
        return self._primary_ball

    @property
    def my_paddle(self) -> ActorSummary:
        if self._my_paddle is None:
            if self.paddle_type is PaddleType.LEFT:
                the_paddle = next(
                    filter(lambda actor: actor.actor_type is ActorType.LEFT_PADDLE, self._game_state.actors), None)
            else:
                the_paddle = next(
                    filter(lambda actor: actor.actor_type is ActorType.RIGHT_PADDLE, self._game_state.actors), None)
            if the_paddle:
                self._my_paddle = actor_to_summary(the_paddle, self.transform)
        return self._my_paddle

    @property
    def opponent_paddle(self) -> Actor:
        if self._opponent_paddle is None:
            if self.paddle_type is PaddleType.LEFT:
                the_paddle = next(
                    filter(lambda actor: actor.actor_type is ActorType.RIGHT_PADDLE, self._game_state.actors), None)
            else:
                the_paddle = next(
                    filter(lambda actor: actor.actor_type is ActorType.LEFT_PADDLE, self._game_state.actors), None)
            if the_paddle:
                self._opponent_paddle = actor_to_summary(the_paddle, self.transform)
        return self._oppenent_paddle

    @property
    def my_scorecard(self) -> ScoreCard:
        return self._game_state.left_scorecard if self.paddle_type is PaddleType.LEFT else self._game_state.right_scorecard

    @property
    def opponent_scorecard(self) -> ScoreCard:
        return self._game_state.left_scorecard if self.paddle_type is PaddleType.RIGHT else self._game_state.right_scorecard
