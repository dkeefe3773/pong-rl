from proto_gen.gamemaster_pb2 import PlayerIdentifier

from config.property_configurator import match_play_config

POINTS_PER_MATCH = match_play_config.points_per_match

def hashable_id(player: PlayerIdentifier) -> str:
    return ":".join([player.player_name, player.paddle_strategy_name])

class StandardScoreCard:
    def __init__(self, player_identifier: PlayerIdentifier, current_match_points_won: int = 0, total_points_won: int = 0,
                 matches_won: int = 0):
        """

        :param player_identifier:            identifier object for the player that this score card represents
        :param current_match_points_won:     the number of points in the current match
        :param total_points_won:             the total number of points won across all matches
        :param matches_won:                  the total number of matches won
        """
        self.player_identifier = player_identifier
        self._current_match_points_won = current_match_points_won
        self._total_points_won = total_points_won
        self._matches_won = matches_won

    @property
    def match_score(self) -> int:
        return self._current_match_points_won

    @property
    def total_points(self) -> int:
        return self._total_points_won

    @property
    def total_matches(self) -> int:
        return self._matches_won

    def add_match_point(self) -> bool:
        """
        Call into this method to allocate a point to a player
        :return:  True if this player wins a match
        """
        match_win = False
        self._total_points_won += 1
        self._current_match_points_won += 1

        if self._current_match_points_won == POINTS_PER_MATCH:
            match_win = True
            self._current_match_points_won = 0
            self._matches_won += 1
        return match_win

    def match_over(self):
        """
        Call into this if the oppenent has one a match
        :return:  None
        """
        self._current_match_points_won = 0

class ScoreKeeper:
    def __init__(self, player1: PlayerIdentifier, player2: PlayerIdentifier):
        """

        :param player1:   first player
        :param player2:   second player
        """
        self.player_to_scorecard = {hashable_id(player1) : StandardScoreCard(player1),
                                    hashable_id(player2) : StandardScoreCard(player2)}

    def tally_point(self, winning_player: PlayerIdentifier, losing_player: PlayerIdentifier):
        """

        :param winning_player:   the winning player
        :param losing_player:    the losing player
        :return: None
        """
        winning_scorecard = self.player_to_scorecard[hashable_id(winning_player)]
        if winning_scorecard.add_match_point():
            losing_scorecard = self.player_to_scorecard[hashable_id(losing_player)]
            losing_scorecard.match_over()

    def get_scorecard(self, player: PlayerIdentifier) -> StandardScoreCard:
        """
        :param player:  the player indentifier
        :return:  the current scorecard of the player
        """
        return self.player_to_scorecard[hashable_id(player)]




