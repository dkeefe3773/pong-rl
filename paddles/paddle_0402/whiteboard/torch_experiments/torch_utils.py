import os
from pathlib import Path

PONG_HOME_PATH = Path(os.environ.get('PONG_HOME'))
TORCHVISION_DATA_PATH = PONG_HOME_PATH / "data" / "torchvision"
