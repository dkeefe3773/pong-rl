from abc import ABC, abstractmethod
from typing import List, Dict, Tuple

import numpy
from matplotlib import pylab
from numpy import random
from sklearn.datasets import load_digits
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from config import logging_configurator
from paddles.paddle_0402.config.paddle_configurator import nmist_raw_ann_config

logger = logging_configurator.get_logger(__name__)

"""
See Adventures in Machine Learning: neural-networks-tutorial https://adventuresinmachinelearning.com/neural-networks-tutorial/
for a great tutorial that goes thru all this math
"""


def plot_sigmoid() -> None:
    """
    Will plot a sigmoid activation function without offset
    :return: None
    """
    x = numpy.arange(-8, 8, 0.1)
    f = 1 / (1 + numpy.exp(-x))
    pylab.plot(x, f)
    pylab.xlabel('x')
    pylab.ylabel('f(x)')
    pylab.show()


def plot_cost_function(iterations_costs: list) -> None:
    """
    will plot the cost function so you can see how cost decreases from iteration to iteration.  The elbow
    will be the sweet spot
    :param iterations_costs: a list whose elements are the cost: norm(y_prediction, actual) for every iteration
    of the artifical neural network
    :return:  None
    """
    pylab.plot(iterations_costs)
    pylab.ylabel('Average Cost Per Iteration')
    pylab.xlabel('Iteration number')
    pylab.show()


def sigmoid_activation(aggregate: numpy.ndarray) -> float:
    """

    :param aggregate: an array whose elements are the aggregate of all the inputs from the previous layer.
    For instance, the first element of the array is the aggregate of all input coming into the first node,
    the second element of the array is the aggregate of all input coming into the second node, and so on.
    By aggregate, we just mean the Z value.  (The sum of all inputs into a node scaled by the weights)
    :return: an array of same size as aggregate whose elements are the applied sigmoid on the aggregate
    """
    # note, numpy.exp can operate on arrays.  It will take the exponential of each element in the array
    return 1 / (1 + numpy.exp(-aggregate))


def sigmoid_derivative(value: numpy.ndarray) -> float:
    """

    :param value: array of numbers
    :return: array of same size as input, with applied sigmoid derivative.  This is used during back propogation
    """
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
    it is seen the neural network back propogation converges faster (and needs less data) when the input data
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
    accumulate partial derivative values for each weight
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
    return -(actual - predicted) * sigmoid_derivative(incoming_aggregation)


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


def create_mini_batches(input_samples: numpy.ndarray, output_samples: numpy.ndarray, batch_size: int) -> List[
    Tuple[numpy.ndarray, numpy.ndarray]]:
    """
    :param input_samples: matrix whose rows are training input samples
    :param training_samples: matrix whose rows are training output samples
    :param batch_size: the number of samples per mini-batch
    :return: a list of mini-batches.  Each list element is a 2-tuple whose first element is the input samples and
    whose second element are the associated output samples.  Each mini-batches input/output samples are of size
    batch_size
    """
    num_samples = len(output_samples)

    # random_ids will be a random list of sample ids
    random_ids = random.choice(num_samples, num_samples, replace=False)

    # now to shuffle the samples
    input_samples_shuffled = input_samples[random_ids, :]
    output_samples_shuffled = output_samples[random_ids, :]
    mini_batches = [(input_samples_shuffled[index:index + batch_size],
                     output_samples_shuffled[index:index + batch_size])
                    for index in range(0, num_samples, batch_size)]
    return mini_batches



# load the nmist data
logger.info("Loading nmist data")
digits = load_digits()

# scaled data has shape (data_count, 64)
logger.info("Scaling nmist data")
scaled_data = scale_data(digits.data)

# lets split our data into training and test bins
logger.info("Splitting nmist data into training and test tests")
input_training, input_testing, label_training, label_testing = train_test_split(scaled_data, digits.target,
                                                                                test_size=0.4)

# lets convert our target labels to be in vector form.  The labels are just 3, 4, etc -- whatever the digit
# is.  Lets convert the output to a 10 deep array with all elements zero except for the digit which is 1
# output will have shape (data_count, 10)
output_training = numpy.zeros((len(label_training), 10))
for label_index, label in enumerate(label_training):
    output_training[label_index, label] = 1

output_testing = numpy.zeros((len(label_testing), 10))
for label_index, label in enumerate(label_testing):
    output_testing[label_index, label] = 1


class Ann(ABC):
    def __init__(self):
        self.avg_cost_for_iterations: list = []

        # lets initialize the weight matrices and the bias vectors for each layer
        logger.info("Initializing network topgrapy and initializing weight matrices and bias vectors for every layer")
        self.network_layer_sizes: list = nmist_raw_ann_config.network_size
        self.num_layers: int = len(self.network_layer_sizes)
        self.weight_matrix_by_layer: Dict[int, numpy.ndarray] = generate_random_weights(self.network_layer_sizes)
        self.bias_by_layer: Dict[int, numpy.ndarray] = generate_random_biases(self.network_layer_sizes)

    @abstractmethod
    def train(self) -> None:
        """
        Implementations will train the weight matrix by layer and the bias by layer on the nmist digit data
        :return:
        """
        pass

    def evalulate_network(self) -> None:
        # this is an array whose elements are the predicted digit
        predicted_labels = numpy.zeros((len(input_testing),))
        for index, test_sample in enumerate(input_testing):
            layer_outputs, layer_aggregates = \
                brute_force_feed_forward(numpy.transpose(test_sample), self.weight_matrix_by_layer, self.bias_by_layer)
            predicted_labels[index] = numpy.argmax(layer_outputs[self.num_layers])
        prediction_accuracy = accuracy_score(label_testing, predicted_labels) * 100
        logger.info(f"Prediction accuracy is {prediction_accuracy}%")
