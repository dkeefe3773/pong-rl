from injections.providers import PlayerProviders
from player import serverstub
from player.controller import PlayerController


def start_player():
    player: PlayerController = PlayerProviders.right_player()
    player.start_playing()


if __name__ == '__main__':
    start_player()
    serverstub.close_global_channel()
