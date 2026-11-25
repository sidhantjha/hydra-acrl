#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 2 ]]; then
  echo 'Usage: export_dsg.sh RUN_DIRECTORY NEW_OUTPUT_JSON' >&2
  exit 2
fi
[[ -f "$1/.mapping.lock" ]] || { echo "No managed mapping run at $1" >&2; exit 1; }
exec flock --shared "$1/.mapping.lock" python3 -B "$(dirname -- "${BASH_SOURCE[0]}")/export_dsg.py" "$@"
