import numpy

from config import logging_configurator
from paddles.paddle_0402.config.paddle_configurator import nmist_raw_ann_config
from paddles.paddle_0402.whiteboard.nmist.ann_regularized import RegularizedNeuralNetwork
from paddles.paddle_0402.whiteboard.nmist.ann_utilities import output_training, \
    plot_cost_function, initialize_gradient_weight_accumulation_matrices, initialize_bias_accumulation_vectors, \
    input_training, brute_force_feed_forward, calculate_outer_layer_gradient, calculate_previous_layer_gradient, \
    create_mini_batches

logger = logging_configurator.get_logger(__name__)


class MiniBatchStochasticGradientDescent(RegularizedNeuralNetwork):
    """
    see: https://adventuresinmachinelearning.com/stochastic-gradient-descent/
    An SGD back propogation is shown to outperform a standard ANN, with marked improvement in convergence time.  However,
    the accuracy can be worse, if only a little.  This is due to the noise of adjusting the weights for every sample.

    The best strategy of all is to NOT adjust weights for every sample but instead to do mini-batch processing, where
    each iteration will draw some small subset of the total samples (randomly) and then perform the aggregate gradient
    delta calculation on the batch.  At the end of the batch, the weights of the network are adjusted.

    This combines SGD and traditional ANN.  This gives the best prediction accuracy.  Additionally, this would
    lend itself to parallization across the mini-batches.

    This gives around a 96% accuracy
    """

    def __init__(self) -> None:
        super().__init__()
        self.batch_size: int = nmist_raw_ann_config.mini_batch_size

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

            # create our mini-batches
            mini_batches = create_mini_batches(input_training, output_training, self.batch_size)
            for mini_batch in mini_batches:
                batch_input = mini_batch[0]
                batch_output = mini_batch[1]

                # now loop thru every sample in the mini-batch
                for sample_index in range(len(batch_output)):
                    # first do a feed forward and collect the aggregates into each layer and the output of each layer
                    # the chained partial derivatives use these
                    sample = batch_input[sample_index, :]
                    layer_outputs, layer_aggregates = brute_force_feed_forward(sample, self.weight_matrix_by_layer,
                                                                               self.bias_by_layer)

                    # keep a running total of our sample costs
                    sample_cost = numpy.linalg.norm(batch_output[sample_index, :] - layer_outputs[self.num_layers])
                    avg_cost_for_iteration += sample_cost
                    # lets perform back propagation, starting from the output layer and working backwards to
                    # distribute the loss across the weights and biases in the network
                    outer_layer_index = self.num_layers
                    outer_layer_gradient = calculate_outer_layer_gradient(batch_output[sample_index, :],
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

                # adjust the weights along their gradients by the step size due to this mini-batch
                self._adjust_weights(gradient_for_weights, gradient_for_bias)

            # keep track of our cost
            avg_cost_for_iteration /= num_samples
            self.avg_cost_for_iterations.append(avg_cost_for_iteration)


if __name__ == "__main__":
    neural_network = MiniBatchStochasticGradientDescent()
    neural_network.train()
    neural_network.evalulate_network()
    plot_cost_function(neural_network.avg_cost_for_iterations)
