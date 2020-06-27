from typing import Dict

import numpy

from config import logging_configurator
from paddles.paddle_0402.config.paddle_configurator import nmist_raw_ann_config
from paddles.paddle_0402.whiteboard.nmist.ann_regularized import RegularizedNeuralNetwork
from paddles.paddle_0402.whiteboard.nmist.ann_utilities import output_training, \
    plot_cost_function, initialize_gradient_weight_accumulation_matrices, initialize_bias_accumulation_vectors, \
    input_training, brute_force_feed_forward, calculate_outer_layer_gradient, calculate_previous_layer_gradient
from paddles.paddle_0402.whiteboard.nmist.simple_ann import SimpleNeuralNetwork

logger = logging_configurator.get_logger(__name__)


class StochasticGradientDescent(RegularizedNeuralNetwork):
    """
    see: https://adventuresinmachinelearning.com/stochastic-gradient-descent/
    A traditional ANN updates an aggregated cost term, without updating the weights of the network, by looping through
    all training points and applying gradient descent for each point.  However, this is done by holding the weights
    of the network static.  Only after all training points have been applied will the weights of the network be
    updated in gross.  Then the next iteration is started that does the same thing and so on.

    However, it has been shown that you get better performance if you update the weights of the network, in mass, for every
    single point.  So rather than caching an aggregated cost term that is applied at the end of an iteration to
    adjust the weights, the network weights are adjusted at the time of the back propagation of every training
    datum.

    This technique is called 'stochastic gradient descent'.  Stochastic because the draw order of the data in the
    training set is supposed to be random for every iteration.  (We won't do that below, but even without the
    shuffled draw from iteration to iteration, updating weights every sample point still improves results)

    This gives about 95% prediction accuracy.
    """

    def __init__(self) -> None:
        super().__init__()

    def train(self):
        num_samples = len(output_training)
        logger.info(
            f"Starting training with {self.num_training_iterations} iterations. Each iteration has {num_samples} samples")
        for training_index in range(self.num_training_iterations):
            avg_cost_for_iteration: float = 0
            if training_index % 50 == 0 and training_index != 0:
                logger.info(
                    f"Done with {training_index} / {self.num_training_iterations} iterations.  Avg cost: {self.avg_cost_for_iterations[-1]}")
            gradient_for_weights = initialize_gradient_weight_accumulation_matrices(self.network_layer_sizes)
            gradient_for_bias = initialize_bias_accumulation_vectors(self.network_layer_sizes)

            # now loop thru every sample
            for sample_index in range(len(output_training)):
                # first do a feed forward and collect the aggregates into each layer and the output of each layer
                # the chained partial derivatives use these
                sample = input_training[sample_index, :]
                layer_outputs, layer_aggregates = brute_force_feed_forward(sample, self.weight_matrix_by_layer,
                                                                           self.bias_by_layer)

                # keep a running total of our sample costs
                sample_cost = numpy.linalg.norm(output_training[sample_index, :] - layer_outputs[self.num_layers])
                avg_cost_for_iteration += sample_cost
                # lets perform back propagation, starting from the output layer and working backwards to
                # distribute the loss across the weights and biases in the network
                outer_layer_index = self.num_layers
                outer_layer_gradient = calculate_outer_layer_gradient(output_training[sample_index, :],
                                                                      layer_outputs[outer_layer_index],
                                                                      layer_aggregates[outer_layer_index])
                gradients_by_layer = {outer_layer_index: outer_layer_gradient}
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
                    gradient_for_bias[layer_index] += gradients_by_layer[layer_index + 1]

                # adjust the weights along their gradients by the step size due to this single sample
                self._adjust_weights(gradient_for_weights, gradient_for_bias)

            avg_cost_for_iteration /= num_samples
            self.avg_cost_for_iterations.append(avg_cost_for_iteration)

if __name__ == "__main__":
    neural_network = StochasticGradientDescent()
    neural_network.train()
    neural_network.evalulate_network()
    plot_cost_function(neural_network.avg_cost_for_iterations)
