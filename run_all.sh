#!/usr/bin/env bash
# Rebuild every level + the shared climber. BLENDER=/path/to/blender ./run_all.sh [-- options]
set -e
cd "$(dirname "$0")"
"${BLENDER:-blender}" -b --python render_levels.py -- "$@"
