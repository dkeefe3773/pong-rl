import sys
from pathlib import Path

# see https://github.com/protocolbuffers/protobuf/issues/1491
# tldr: proto-c compiler is expecting your idl and compiled files to be in same directory.  If you don't do that,
# imports will be broken.  This is a fix to add proto_gen to the python path for imports
sys.path.append(str(Path(__file__).parent))