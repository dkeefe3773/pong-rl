import logging.config
from pathlib import Path

true_path = Path(__file__).parent / 'logging.conf'
logging.config.fileConfig(str(true_path.resolve()))


def get_logger(name):
    return logging.getLogger(name)
