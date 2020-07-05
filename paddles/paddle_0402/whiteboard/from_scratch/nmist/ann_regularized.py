from typing import Dict

import numpy

from config import logging_configurator
from paddles.paddle_0402.config.paddle_configurator import nmist_raw_ann_config
from paddles.paddle_0402.whiteboard.from_scratch.nmist import output_training, \
    plot_cost_function
from paddles.paddle_0402.whiteboard.from_scratch.nmist import SimpleNeuralNetwork

logger = logging_configurator.get_logger(__name__)


class RegularizedNeuralNetwork(SimpleNeuralNetwork):
    """
    see: https://adventuresinmachinelearning.com/category/deep-learning/neural-networks/ for a discussion
    of regularization

    This gives a prediction accuracy of about 93% after 3000 iterations.

    This is the same as the simple ariticial neural network, EXCEPT that we will adjust our cost function
    to keep the weights small.  A network with large weights will have nodes whose activation is dominated by
    a singular output from the previous layer node.  In other words, the aggregate term going into the activation
    function will be dominated by the high weight terms.  During training, the network can latch onto these large
    weights and reinforce them at the expense of dampening the other input signals.

    Another way to think about this is that high weights are essentially 'latching' onto certain aspects of the data,
    in a very strong way.  It is overfitting to the training data set.

    It is seen that, generally, keeping weights small improves network prediction performance.

    Back propogation is based upon minimizing the overall cost across all samples.  We can simply add a term
    to the cost to account for the weights
    COST = (1/2) * (1/sample_count) SUM_OVER_SAMPES_Z[(abs(label - predicted)^2 + gamma/2 SUM[all_weights]^2

    If you do the math, the gradients of the weights don't change.  However, the update step does change:
    new_weights_layer_l = old_weights_layer_l - alpha[1/sample_size * gradient_weights_layer_l + gamma * weights_layer_l]
    """

    def __init__(self) -> None:
        super().__init__()
        self.regularization_lambda: float = nmist_raw_ann_config.regularization_lambda

    def _adjust_weights(self, gradient_for_weights: Dict[int, numpy.ndarray],
                        gradient_for_bias: Dict[int, numpy.ndarray]) -> None:
        """
        This adjusts the weights according to a regularization optimzation function, whereby the cost to minimize
        contains an additional term to minimize the quadrature of all weights in the network.
        :param gradient_for_weights:   a dict whose key is network layer and whose value is a weight matrix
        :param gradient_for_bias:  a dict whose key is the network layer and whose value is the vector of gradients
        :return:
        """
        for layer_index in range(self.num_layers - 1, 0, -1):
            self.weight_matrix_by_layer[layer_index] += -self.step_size * (
                    1.0 / len(output_training) * gradient_for_weights[layer_index] + self.regularization_lambda *
                    self.weight_matrix_by_layer[layer_index])
            self.bias_by_layer[layer_index] += -self.step_size * (
                    1.0 / len(output_training) * gradient_for_bias[layer_index])


if __name__ == "__main__":
    neural_network = RegularizedNeuralNetwork()
    neural_network.train()
    neural_network.evalulate_network()
    plot_cost_function(neural_network.avg_cost_for_iterations)
