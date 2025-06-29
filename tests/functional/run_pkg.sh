#!/usr/bin/env bash
set -Eeuo pipefail

# Runs the following:
# 1. Creates a temporary directory
# 2. Sets up a Python virtual environment in that directory
# 3. Installs the package from the local wheel file
# 4. Run the proxy

CURRENT_DIR=$(dirname "$(realpath "$0")")
TMP_DIR=$(mktemp -d -t passage.XXXXXXXX)     # e.g. /tmp/mytask.X8i6TZ0p
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT INT TERM
echo "Using temp dir: $TMP_DIR"

cd "$TMP_DIR" || exit 1

python3 -m venv venv
source venv/bin/activate

pip install $CURRENT_DIR/../../dist/prompt_passage-*.whl

prompt-passage

echo "DONE!"