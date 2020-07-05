from typing import Dict

import numpy

from config import logging_configurator
from paddles.paddle_0402.config.paddle_configurator import nmist_raw_ann_config
from paddles.paddle_0402.whiteboard.from_scratch.nmist import Ann, output_training, \
    initialize_gradient_weight_accumulation_matrices, initialize_bias_accumulation_vectors, input_training, \
    brute_force_feed_forward, calculate_outer_layer_gradient, calculate_previous_layer_gradient, plot_cost_function

logger = logging_configurator.get_logger(__name__)


class SimpleNeuralNetwork(Ann):
    """
    With 3000 iterations, this gives 86% prediction accuracy.

    This is as simple as it gets.  Back propogation is based upon minimizing the overall cost across all samples:
    COST = (1/2) * (1/sample_count) SUM_OVER_SAMPES_Z[(abs(label - predicted)^2
    """
    def __init__(self) -> None:
        super().__init__()
        self.num_training_iterations: int = nmist_raw_ann_config.training_iterations
        self.step_size: float = nmist_raw_ann_config.gradient_step_size

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

            # adjust the weights along their gradients by the step size
            self._adjust_weights(gradient_for_weights, gradient_for_bias)
            avg_cost_for_iteration /= num_samples
            self.avg_cost_for_iterations.append(avg_cost_for_iteration)

    def _adjust_weights(self, gradient_for_weights: Dict[int, numpy.ndarray],
                        gradient_for_bias: Dict[int, numpy.ndarray]) -> None:
        """
        This adjusts the weights according to the optimization function to minimize the quadrature of
        residuals from predicted to labeled, normalized by the sample data count
        :param gradient_for_weights:  a dict whose key is the network layer and whose value is a weight matrix
        :param gradient_for_bias:  a dict whose key is the network layer and whose value is vector of bias gradients
        :return:
        """
        for layer_index in range(self.num_layers - 1, 0, -1):
            self.weight_matrix_by_layer[layer_index] += -self.step_size * (
                    1.0 / len(output_training) * gradient_for_weights[layer_index])
            self.bias_by_layer[layer_index] += -self.step_size * (
                    1.0 / len(output_training) * gradient_for_bias[layer_index])


if __name__ == "__main__":
    neural_network = SimpleNeuralNetwork()
    neural_network.train()
    neural_network.evalulate_network()
    plot_cost_function(neural_network.avg_cost_for_iterations)
