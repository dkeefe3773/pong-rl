import numpy as np
from tensorflow import keras
import os
from pathlib import Path
from dataclasses import dataclass

from config import logging_configurator
from paddles.memory import Memory
from paddles.paddle import PaddleController
from paddles.paddle_utils import GameStateWrapper
from proto_gen.gamemaster_pb2 import PaddleType, GameStateBuffer, PaddleDirective, PaddleAction, GameState

from .simple_dqn_model import build_model

logger = logging_configurator.get_logger(__name__)

index_to_directive = [PaddleDirective.UP, PaddleDirective.DOWN, PaddleDirective.STATIONARY]


def prediction_to_directive(prediction: np.ndarray):
    max_index: int = np.argmax(prediction)
    return index_to_directive[max_index]


class NNState:
    def __init__(self, state_wrapper: GameStateWrapper):
        primary_ball = state_wrapper.primary_ball
        my_paddle = state_wrapper.my_paddle
        op_paddle = state_wrapper.opponent_paddle
        op_x, op_y = (op_paddle.shape.centroid.x, op_paddle.shape.centroid.y) \
            if op_paddle is not None else (600, 400 / 2)

        self.ball_pos = np.asarray((primary_ball.shape.centroid.x, primary_ball.shape.centroid.y)).round()
        self.ball_v = np.asarray((primary_ball.vel.vel_x, primary_ball.vel.vel_y)).round()
        self.player_pos = np.asarray((my_paddle.shape.centroid.x, my_paddle.shape.centroid.y)).round()
        self.op_pos = np.asarray((op_x, op_y)).round()
        self.op_score_total = state_wrapper.opponent_scorecard.total_points
        self.player_score_total = state_wrapper.my_scorecard.total_points

    def to_np_array(self):
        return np.array([[self.ball_v[0], self.ball_v[1],
                          self.ball_pos[0], self.ball_pos[1],
                          self.player_pos[0], self.player_pos[1],
                          self.op_pos[0], self.op_pos[1]]])

    def dist_player_to_ball(self) -> float:
        dist = np.linalg.norm(self.ball_pos - self.player_pos)
        return dist

    def dist_op_to_ball(self) -> float:
        dist = np.linalg.norm(self.ball_pos - self.op_pos)
        return dist

    def y_dist_player_to_ball(self):
        return abs(self.player_pos[1] - self.ball_pos[1])

    def returning_ball(self) -> bool:
        return self.ball_v[0] < 0

    def op_score(self):
        return self.op_score_total

    def player_score(self):
        return self.player_score_total


@dataclass
class OutInfo:
    dir: Path
    model_name: Path
    steps: int

    def init_path(self):
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def check_write(self, iteration: int, model):
        if iteration > 0 and iteration % self.steps == 0:
            model.save(self.dir / self.model_name)


class SimpleDQNTrainingPaddle(PaddleController):
    def __init__(self, paddle_type: PaddleType,
                 out_dir=Path(__file__).parent / 'models',
                 out_model_name=Path("simple_model.hd5"),
                 out_steps=1000):
        super().__init__(paddle_type)
        self.model = build_model()
        self.memory = Memory(max=10_000)
        self.partial_exp = {
            'prev': None,
            'action': None
        }
        self.training_counter = 0
        self.out_counter = 0
        self.discount_rate = 0.95
        self.learning_count = 10
        self.epsilon = 0.2
        self.out_info = OutInfo(out_dir, out_model_name, out_steps)
        self.out_info.init_path()

    def process_game_state(self, game_state_buffer: GameStateBuffer):
        self.game_state_wrapper.game_state = game_state_buffer.game_states[-1]

        new_state = {
            'state': NNState(self.game_state_wrapper),
            'my_scorecard': self.game_state_wrapper.my_scorecard,
            'op_scorecard': self.game_state_wrapper.opponent_scorecard
        }

        self.complete_exp(new_state)
        action = PaddleDirective.STATIONARY
        if new_state is not None:
            if np.random.random() < self.epsilon:
                self.epsilon = max((self.epsilon * 0.99995), 0.01)
                # logger.info(f'Epsilon: {self.epsilon}')
                action = np.random.randint(0, 3)
            else:
                prediction = self.model.predict_on_batch([new_state['state'].to_np_array()])[0]
                action = prediction_to_directive(prediction=prediction)
            self.partial_exp = {'prev': new_state, 'action': action}
            if self.training_counter >= 10:
                # logger.info(f'Epsilon: {self.epsilon}')
                self.training_counter = 0
                self.train()
            self.out_counter += 1
            self.out_info.check_write(self.out_counter, self.model)
        else:
            logger.error("State is none.")
        return PaddleAction(paddle_directive=action)

    def complete_exp(self, state: GameState):
        if self.partial_exp['prev'] is not None:
            prev, act = self.partial_exp['prev'], self.partial_exp['action']
            reward, terminal = self.compute_reward(prev, state)
            self.memory.add_memory(
                (prev['state'].to_np_array(), act, reward, state['state'].to_np_array(), terminal)
            )
            self.training_counter += 1

    def compute_reward(self, prev: GameState, state: GameState):
        prev_state: NNState = prev['state']
        curr_state: NNState = state['state']

        player_scored = (curr_state.player_score() != prev_state.player_score())
        op_scored = (curr_state.op_score() != prev_state.op_score())
        terminal = op_scored or player_scored

        y_dist = curr_state.y_dist_player_to_ball()
        prev_y_dist = prev_state.y_dist_player_to_ball()
        # dist_reward = 500 - y_dist
        dist_reward = prev_y_dist - y_dist
        # dist_reward = 0 #prev_y_dist - y_dist

        reward = dist_reward if not terminal else 0

        if op_scored:
            reward = -prev_y_dist
            # reward = -y_dist
            # reward = -10_000 - y_dist

        # logger.info(f"dist_reward: {dist_reward:0.3f}")

        return reward, terminal

    def train(self):
        count = self.learning_count
        experiences = self.memory.sample(count)
        for prev_state, action, reward, next_state, terminal in experiences:
            q_update = reward if terminal else (
                        reward + self.discount_rate * np.amax(self.model.predict_on_batch(next_state)[0]))
            q_values = self.model.predict_on_batch(prev_state)
            q_values[0][action] = q_update
            self.model.fit(prev_state, q_values, verbose=0)


class SimpleDQNTrainedPaddle(PaddleController):

    def __init__(self, paddle_type: PaddleType,
                 model_file=Path(__file__).parent / 'models' / 'simple_model.hd5'):
        super().__init__(paddle_type)
        self.model = keras.models.load_model(model_file)
        logger.info(f"Loading dqn model: {model_file}")


    def process_game_state(self, game_state_buffer: GameStateBuffer):
        self.game_state_wrapper.game_state = game_state_buffer.game_states[-1]

        state = NNState(self.game_state_wrapper)

        prediction = self.model.predict_on_batch([state.to_np_array()])[0]
        action = prediction_to_directive(prediction=prediction)
        return PaddleAction(paddle_directive=action)
