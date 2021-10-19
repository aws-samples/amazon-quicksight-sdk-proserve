#! /bin/bash

set -e
set -u
set -o pipefail

cd ../app/

echo ''
python3 -m pytest test.py
