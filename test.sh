#!/bin/bash

# Validates the plugin manifest and checks the shell scripts parse.

set -euo pipefail
cd "$(dirname "$0")"

omarchy-plugin-validate .

for script in browser/*.sh workspace/*.sh; do
  bash -n "$script"
done

python3 -m py_compile research/dispatcher.py
echo "ok"
