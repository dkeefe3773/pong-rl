import unittest
from typing import List, Dict, Tuple

import numpy
from matplotlib import pylab
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from paddles.paddle_0402.config.paddle_configurator import nmist_raw_ann_config

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


def sigmoid_activation(aggregate: numpy.ndarray) -> float:
    # note, numpy.exp can operate on arrays.  It will take the exponential of each element in the array
    return 1 / (1 + numpy.exp(-aggregate))


def sigmoid_derivative(value: numpy.ndarray) -> float:
    return sigmoid_activation(value) * (1 - sigmoid_activation(value))


def brute_force_feed_forward(input: numpy.ndarray,
                             layer_weights: Dict[int, numpy.ndarray],
                             bias_weights: Dict[int, numpy.ndarray]) -> Tuple[
    Dict[int, numpy.ndarray], Dict[int, numpy.ndarray]]:
    """
    :param input:          input_n x 1 array.  1D array for the input.
    :param layer_weights:  a dict of weight matrices for every layer.  So, the matrix for l=1 will be
    the weight matrix for the weights on the input layer, and so on.
    Each row of the weight matrix represents all the weights going into a single node into layer l+1.
    Each col represents all the weights going out of a single node from layer l.
    As an example, for a 3-layer network (input, one hidden layer, output) where input layer has 3
    nodes, hidden layer has 3 nodes, and output layer has a single node will have two weight matrices:
    layer_weights = [w1, w2]  where w_i_j notation means i==> node in next layer, j ==> node in current layer.
    W_layer_(l)_to_(l+1) = [ w11    w12    w13]
                           [ w21    w22    w23]
                           [ w31    w32    w33]

    :param bias_weights: dict of 1D arrays for the bias weights of the layer.  For our 3-layer network:
    bias_weights = [b1, b2] where
    b1 = [a b c]^T
    and b2 = [d]
    :return: a 2-tuple whose first element is a dict by layer of 1D array of the layer outputs and whose
    second element is a dict by layer of the 1-D array of aggregated inputs for each layer (for convenience)
    """

    # according to tradition, the input layer is layer 1 (not zero), which causes no end of headaches for indexing
    outputs_by_layer = {1: input}
    aggregates_by_layer = {}
    num_layers = len(layer_weights) + 1
    output_from_next_layer = None
    for layer_index in range(1, num_layers):
        layer_weight_matrix = layer_weights[layer_index]  # weights going from layer (l) to (l+1)
        layer_bias_weights = bias_weights[layer_index]  # bias terms going into (l+1) layer
        layer_input = input if output_from_next_layer is None else output_from_next_layer
        aggregates_next_layer = layer_weight_matrix.dot(layer_input) + layer_bias_weights
        output_from_next_layer = sigmoid_activation(aggregates_next_layer)
        aggregates_by_layer[layer_index + 1] = aggregates_next_layer
        outputs_by_layer[layer_index + 1] = output_from_next_layer
    return outputs_by_layer, aggregates_by_layer


def scale_data(input_data: numpy.ndarray) -> numpy.ndarray:
    """
    It is common to scale the input data for a neural network to be between  [0,1] or [-1,1].  This is because
    it is seen the neurel network back propogation converges faster (and needs less data) when the input data
    is on the same scale.  Otherwise, weights will vary wildly from input data element to input data element and
    this leads to longer convergence time.
    :param input_data: 2d numpy array of shape (num_samples, num_features)
    :return: 2d numpy array where features have had their mean subtracted and normalized to their standard deviation.
             In other words, most features will end up being between [-1, 1] with some outliers.
    """
    scaler = StandardScaler()
    return scaler.fit_transform(input_data.data)


def generate_random_weights(network_layer_sizes: List[int]) -> Dict[int, numpy.ndarray]:
    """
    :param network_layer_sizes: list of sizes for each network layer
    :return: a dict whose keys are the layers (layer 1 is the input layer) and whose
    values are the weight matrix between layer l and layer l+1
    """
    num_layers = len(network_layer_sizes)
    weight_matrix_by_layer = {}
    for layer_index in range(0, num_layers - 1):
        # each row are the incoming weights coming into a single node in layer l+1
        # each column are all the weights coming out of a single node from layer l
        num_nodes_this_layer = network_layer_sizes[layer_index]
        num_nodes_next_layer = network_layer_sizes[layer_index + 1]
        weights = numpy.random.random_sample((num_nodes_next_layer, num_nodes_this_layer))

        # it is common nomenclature to refer to the first layer as layer 1 (rather than layer zero)
        weight_matrix_by_layer[layer_index + 1] = weights
    return weight_matrix_by_layer


def generate_random_biases(network_layer_sizes: List[int]) -> Dict[int, numpy.ndarray]:
    """
    :param network_layer_sizes: list of sizes for each network layer
    :return: a dict whose keys are the layers (layer 1 is the input layer) and whose
    values are the bias vectors for the layer
    """
    num_layers = len(network_layer_sizes)
    bias_vectors_by_layer = {}
    for layer_index in range(1, num_layers):
        # notation for bias terms is a bit odd.  b^l is the bias vector from layer l-1 going into layer l
        bias_vectors_by_layer[layer_index] = numpy.random.random_sample((network_layer_sizes[layer_index],))
    return bias_vectors_by_layer


def initialize_gradient_weight_accumulation_matrices(network_layer_sizes: List[int]) -> Dict[int, numpy.ndarray]:
    """
    :param network_layer_sizes:  list of sizes for each network layer
    :return: zeroed out weight matrices for each each layer.  Meant to be used in backpropagation to 
    accumulate partial derivate values for each weight
    """
    num_layers = len(network_layer_sizes)
    weight_matrix_by_layer = {}
    for layer_index in range(0, num_layers - 1):
        # each row are the incoming weights coming into a single node in layer l+1
        # each column are all the weights coming out of a single node from layer l
        num_nodes_this_layer = network_layer_sizes[layer_index]
        num_nodes_next_layer = network_layer_sizes[layer_index + 1]
        weights = numpy.zeros((num_nodes_next_layer, num_nodes_this_layer))

        # it is common nomenclature to refer to the first layer as layer 1 (rather than layer zero)
        weight_matrix_by_layer[layer_index + 1] = weights
    return weight_matrix_by_layer


def initialize_bias_accumulation_vectors(network_layer_sizes: List[int]) -> Dict[int, numpy.ndarray]:
    """
    :param network_layer_sizes:  list of sizes for each network layer
    :return: zeroed out bias vectors for each each layer.  Meant to be used in backpropagation to 
    accumulate partial derivate values for each bias
    """
    num_layers = len(network_layer_sizes)
    bias_vectors_by_layer = {}
    for layer_index in range(1, num_layers):
        # notation for bias terms is a bit odd.  b^l is the bias vector from layer l-1 going into layer l
        bias_vectors_by_layer[layer_index] = numpy.zeros((network_layer_sizes[layer_index],))
    return bias_vectors_by_layer


def calculate_outer_layer_gradient(actual: numpy.ndarray, predicted: numpy.ndarray,
                                   incoming_aggregation: numpy.ndarray) -> numpy.ndarray:
    """

    :param actual:  the array of values for the labeled data.  10 x 1
    :param predicted: the predicted values 10 x 1
    :param incoming_aggregation: the array of aggregated values coming into each node of the outer layer
           (weight*x * bias) 10 x 1
    :return: an array of the error residual multiplied by the deriviate of the activation function. 10x1
    The math shows that the gradient of the weights of the previous layer are proportional to this product.
    (this is the peculiar form when using sigmoid as the activation function)
    """
    return (actual - predicted) * sigmoid_derivative(incoming_aggregation)


def calculate_previous_layer_gradient(gradient_next_layer: numpy.ndarray,
                                      weight_matrix: numpy.ndarray,
                                      incoming_aggregation: numpy.ndarray) -> numpy.ndarray:
    """
    The chain rule of partial derivatives starting from the outer layer going backwards shows that the
    weights going from layer l to (l+1) have a gradient proportional to the gradients of (l+1) times
    the derivative of the sigmoid evaluated at the aggregation values going into layer l.
    :param gradient_next_layer:  The gradient term from the layer after this one
    :param weight_matrix:        The weight matrix from this layer to the next layer
    :param incoming_aggregation: The aggregated valuues going into each node for this layer. (weight*x + bias)
    :return: The weight matrix * gradient_last_layer * sigmoid derivative at aggregation value
    """
    return numpy.dot(numpy.transpose(weight_matrix), gradient_next_layer) * sigmoid_derivative(incoming_aggregation)


class TestAnn(unittest.TestCase):
    def setUp(self) -> None:
        # get the nmist digits
        digits = load_digits()

        # scaled data has shape (data_count, 64)
        self.scaled_data = scale_data(digits.data)

        # lets split our data into training and test bins
        self.input_training, self.input_testing, self.label_training, self.label_testing = train_test_split(
            self.scaled_data, digits.target, test_size=0.4)

        # lets convert our target labels to be in vector form.  The labels are just 3, 4, etc -- whatever the digit
        # is.  Lets convert the output to a 10 deep array with all elements zero except for the digit which is 1
        # output will have shape (data_count, 10)
        self.output_training = numpy.zeros((len(self.label_training), 10))
        for label_index, label in enumerate(self.label_training):
            self.output_training[label_index, label] = 1

        self.output_testing = numpy.zeros((len(self.label_testing), 10))
        for label_index, label in enumerate(self.label_testing):
            self.output_testing[label_index, label] = 1

        # lets initialize the weight matrices and the bias vectors for each layer
        self.network_layer_sizes = nmist_raw_ann_config.network_size
        self.num_layers = len(self.network_layer_sizes)
        self.weight_matrix_by_layer = generate_random_weights(self.network_layer_sizes)
        self.bias_by_layer = generate_random_biases(self.network_layer_sizes)

    def test_brute_force_feed_forward(self):
        # assume a 3 layer network (3,3,1)
        # each row in the matrix represents the weights coming into one particular node in the next layer
        # each column in the matrix represents all the weights flowing out of one single node in the current layer
        weights_layer_1_2 = numpy.array([[0.2, 0.2, 0.2], [0.4, 0.4, 0.4], [0.6, 0.6, 0.6]])
        weights_layer_2_3 = numpy.array([[0.5, 0.5, 0.5]])
        layer_weights = {1: weights_layer_1_2, 2: weights_layer_2_3}

        bias_weights_layer_1 = numpy.array([0.8, 0.8, 0.8])
        bias_weights_layer_2 = numpy.array([0.2])
        bias_weights = {1: bias_weights_layer_1, 2: bias_weights_layer_2}
        input_array = numpy.array([1.5, 2.0, 3.0])
        layer_outputs, layer_aggregates = brute_force_feed_forward(input_array, layer_weights, bias_weights)
        final_layer_output = layer_outputs[3]
        self.assertAlmostEqual(final_layer_output[0], 0.8354, places=3)

    @unittest.skip
    def test_full_training(self):
        num_training_iterations = nmist_raw_ann_config.training_iterations
        step_size = nmist_raw_ann_config.gradient_step_size
        for training_index in range(num_training_iterations):
            gradient_for_weights = initialize_gradient_weight_accumulation_matrices(self.network_layer_sizes)
            gradient_for_bias = initialize_bias_accumulation_vectors(self.network_layer_sizes)

            # now loop thru every sample
            for sample_index in range(len(self.output_training)):
                # first do a feed forward and collect the aggregates into each layer and the output of each layer
                # the chained partial derivatives use these
                sample = self.input_training[sample_index, :]
                layer_outputs, layer_aggregates = brute_force_feed_forward(sample, self.weight_matrix_by_layer,
                                                                           self.bias_by_layer)

                # lets perform back propagation, starting from the output layer and working backwards to
                # distribute the loss across the weights and biases in the network
                outer_layer_index = self.num_layers
                outler_layer_gradient = calculate_outer_layer_gradient(self.output_training[sample_index, :],
                                                                       layer_outputs[outer_layer_index],
                                                                       layer_aggregates[outer_layer_index])
                gradients_by_layer = {outer_layer_index: outler_layer_gradient}
                for layer_index in range(self.num_layers - 1, 0, -1):
                    if layer_index > 1:
                        inner_layer_gradient = \
                            calculate_previous_layer_gradient(gradients_by_layer[layer_index + 1],
                                                              self.weight_matrix_by_layer[layer_index],
                                                              layer_aggregates[layer_index])
                        gradients_by_layer[layer_index] = inner_layer_gradient
                    gradient_for_weights[layer_index] += numpy.dot(
                        gradients_by_layer[layer_index + 1][:, numpy.newaxis],
                        numpy.transpose(
                            layer_outputs[layer_index][:, numpy.newaxis]))
                    gradient_for_bias += gradients_by_layer[layer_index + 1]

            # adjust the weights along their gradients by the step size
            for layer_index in range(self.num_layers - 1, 0, -1):
                self.weight_matrix_by_layer[layer_index] += -step_size * (
                            1.0 / len(self.output_training) * gradient_for_weights[layer_index])
                self.bias_by_layer[layer_index] += -step_size * (
                            1.0 / len(self.output_training) * gradient_for_bias[layer_index])
