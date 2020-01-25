from typing import Tuple

import numpy
from PIL import Image

from proto_gen.gamemaster_pb2 import ImageFrame


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

class GameStateWrapper():
    

