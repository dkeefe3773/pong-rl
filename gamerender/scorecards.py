from proto_gen.gamemaster_pb2 import PlayerIdentifier


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
        self.current_match_points_won = current_match_points_won
        self.total_points_won = total_points_won
        self.matches_won = matches_won
