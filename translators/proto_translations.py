from __future__ import annotations

import numpy
import pygame

from gameengine.gameactors import Actor, Ball, BallFlavor, Wall, Paddle
from gamerender.scorecards import ScoreKeeper, StandardScoreCard
from proto_gen.gamemaster_pb2 import Actor as ProtoActor, ImageFrame, ScoreCard
from proto_gen.gamemaster_pb2 import GameState, Coord, ActorType, PaddleType


def get_proto_actor_type(game_actor: Actor):
    if isinstance(game_actor, Ball) and game_actor.flavor is BallFlavor.PRIMARY:
        return ActorType.PRIMARY_BALL
    elif isinstance(game_actor, Wall):
        return ActorType.WALL
    elif isinstance(game_actor, Paddle) and game_actor.paddle_type is PaddleType.LEFT:
        return ActorType.LEFT_PADDLE
    elif isinstance(game_actor, Paddle) and game_actor.paddle_type is PaddleType.RIGHT:
        return ActorType.RIGHT_PADDLE
    else:
        return ActorType.UNKNOWN

def create_proto_scorecard(scorecard: StandardScoreCard) -> ScoreCard:
    proto_score_card = ScoreCard()
    proto_score_card.player.CopyFrom(scorecard.player_identifier)
    proto_score_card.current_game_points = scorecard.match_score
    proto_score_card.total_match_points = scorecard.total_matches
    proto_score_card.total_points = scorecard.total_points
    return proto_score_card

class GameStateBuilder:
    def __init__(self):
        self._game_state = GameState()

    def add_game_actor(self, game_actor: Actor) -> GameStateBuilder:
        proto_actor = ProtoActor()
        proto_coords = [Coord(x=int(poly_coord[0]), y=int(poly_coord[1])) for poly_coord in
                        list(game_actor.shape.exterior.coords)]
        proto_actor.coords.extend(proto_coords)
        velocity_coord = Coord(x=int(game_actor.velocity[0]), y = int(game_actor.velocity[1]))
        proto_actor.velocity.CopyFrom(velocity_coord)
        proto_actor.actor_type = get_proto_actor_type(game_actor)
        self._game_state.actors.append(proto_actor)
        return self

    def add_arena_surface(self, arena_surface: pygame.Surface) -> GameStateBuilder:
        # note, it is MUCH faster sending 2d array of encoded 32 bit color integers rather than 3d array of r,g,b
        pixels = numpy.transpose(pygame.surfarray.pixels2d(arena_surface))
        arena_byte_array = numpy.ndarray.tobytes(pixels)
        arena_frame: ImageFrame = ImageFrame(image=arena_byte_array, num_rows=pixels.shape[0], num_cols=pixels.shape[1])
        self._game_state.arena_frame.CopyFrom(arena_frame)
        return self

    def add_scorekeeper(self, scorekeeper: ScoreKeeper) -> GameStateBuilder:
        proto_score_cards = [create_proto_scorecard(scorecard) for scorecard in scorekeeper.get_scorecards()]
        for proto_score_card in proto_score_cards:
            if proto_score_card.player.paddle_type is PaddleType.LEFT:
                self._game_state.left_scorecard.CopyFrom(proto_score_card)
            elif proto_score_card.player.paddle_type is PaddleType.RIGHT:
                self._game_state.right_scorecard.CopyFrom(proto_score_card)
        return self

    def add_state_iteration(self, state_iteration: int):
        self._game_state.state_iteration = state_iteration

    def build(self) -> GameState:
        return self._game_state
