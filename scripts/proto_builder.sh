#!/bin/bash

# This script will invoke the protoc compiler (via the grpc_tools.protoc python module using c-extension for proto-c *.so)
# on a single directory, proto_idl, containing one or more proto files.
# The *.py files will be generated and placed within proto_gen folder.
# It is expected your python path contains the grpc_tools package, available from pip or conda.
set -e

# makes stderr of command be in red (see https://serverfault.com/questions/59262/bash-print-stderr-in-red-color)
color_errors_red()(set -o pipefail;"$@" 2>&1>&3|sed $'s,.*,\e[31m&\e[m,'>&2)3>&1


current_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"
idl_dir=${current_dir}/../proto_idl
generation_dir=${current_dir}/../proto_gen
echo "Processing: compiling proto idl files within: $( cd ${idl_dir} > /dev/null 2>&1 && pwd ) ..."

# proto_path: absolute path to the proto idl files
# python_out: where to place the generated python files for the messages
# grpc_python_out: where to place the generated python files for the services
color_errors_red python -m grpc_tools.protoc --proto_path=${idl_dir} \
                            --python_out=${generation_dir} \
                            --grpc_python_out=${generation_dir} ${idl_dir}/*.proto

echo "Success: Generated artifacts have been placed within: $( cd ${generation_dir} > /dev/null 2>&1 && pwd )"
