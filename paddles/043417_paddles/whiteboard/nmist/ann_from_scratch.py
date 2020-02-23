import math
from typing import List

import numpy
from matplotlib import pylab

import unittest

"""
Creating a network from scratch.  Following tutorian in Adventures in Machine Learning: neural-networks-tutorial
https://adventuresinmachinelearning.com/neural-networks-tutorial/
"""


def plot_sigmoid():
    x = numpy.arange(-8, 8, 0.1)
    f = 1 / (1 + numpy.exp(-x))
    pylab.plot(x, f)
    pylab.xlabel('x')
    pylab.ylabel('f(x)')
    pylab.show()


def sigmoid_activation(aggregate: float) -> float:
    return 1 / (1 + math.exp(-aggregate))


def brute_force_feed_forward(layer_count: int, input: numpy.ndarray, layer_weights: List[numpy.ndarray],
                             bias_weights: List[numpy.ndarray]) -> numpy.ndarray:
    """

    :param layer_count:    the number of layers in the neural net, including the input and output laywers
    :param input:          input_n x 1 array.  1D array for the input.
    :param layer_weights:  a list of weight matrices for every layer.  So, the first element of the list will be
    the weight matrix for the weights on the input layer, and so on.
    Each row of the weight matrix represents all the weights going into a single node into layer l+1.
    Each col represents all the weights going out of a single node from layer l.
    As an example, for a 3-layer network (input, one hidden layer, output) where input layer has 3
    nodes, hidden layer has 3 nodes, and output layer has a single node will have two weight matrices:
    layer_weights = [w1, w2]  where w_i_j notation means i==> node in next layer, j ==> node in current layer.
    W_layer_(l)_to_(l+1) = [ w11    w12    w13]
                           [ w21    w22    w23]
                           [ w31    w32    w33]

    :param bias_weights: list of 1D arrays for the bias weights of the layer.  For our 3-layer network:
    bias_weights = [b1, b2] where
    b1 = [a b c]^T
    and b2 = [d]
    :return: a 1D array of the output layer of the network
    """
    output_from_next_layer = None
    for layer_index in range(layer_count - 1):
        layer_weight_matrix = layer_weights[layer_index]
        layer_bias_weights = bias_weights[layer_index]
        num_nodes_in_next_layer = layer_weight_matrix.shape[0]
        layer_input = input if output_from_next_layer is None else output_from_next_layer

        output_from_next_layer = numpy.zeros((num_nodes_in_next_layer,))
        for node_index in range(num_nodes_in_next_layer):
            # a row of the weight_matrix represents the weights going into a single node of the next layer
            node_weight_array = layer_weight_matrix[node_index, :]

            # this is the input dot product with the corresponding weights.
            aggegrate_value = numpy.dot(node_weight_array, layer_input)

            # now add in the bias for the node
            aggegrate_value += layer_bias_weights[node_index]
            output_from_next_layer[node_index] = sigmoid_activation(aggegrate_value)
    return output_from_next_layer

class TestAnn(unittest.TestCase):
    def test_brute_force_feed_forward(self):
        # assume a 3 layer network (3,3,1)
        # each row in the matrix represents the weights coming into one particular node in the next layer
        # each column in the matrix represents all the weights flowing out of one single node in the current layer
        weights_layer_1_2 = numpy.array([[0.2, 0.2, 0.2], [0.4, 0.4, 0.4], [0.6, 0.6, 0.6]])
        weights_layer_2_3 = numpy.array([[0.5, 0.5, 0.5]])
        layer_weights = numpy.array([weights_layer_1_2, weights_layer_2_3])

        bias_weights_layer_1 = numpy.array([0.8, 0.8, 0.8])
        bias_weights_layer_2 = numpy.array([0.2])
        bias_weights = numpy.array([bias_weights_layer_1, bias_weights_layer_2])
        input_array = numpy.array([1.5, 2.0, 3.0])
        feed_forward_result = brute_force_feed_forward(3, input_array, layer_weights, bias_weights)
        self.assertAlmostEqual(feed_forward_result[0], 0.8354, places=3)


if __name__ == "__main__":
    unittest.main()