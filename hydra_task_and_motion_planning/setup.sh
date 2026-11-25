#!/usr/bin/env bash
set -euo pipefail
export MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1
module=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python=${PYTHON:-python3}
venv=${PLANNING_VENV:-"$module/.venv"}
spark="$module/../hydra_mapping/hydra_ws/src/spark_dsg"
extras=''
usage='Usage: setup.sh [--viz] [--spark-wheel PATH_TO_VERIFIED_WHEEL]'
while (( $# )); do
  case "$1" in
    --viz) extras='[viz]' ;;
    --spark-wheel) [[ $# -ge 2 && -f "$2" ]] || { echo "$usage" >&2; exit 2; }; spark=$2; shift ;;
    -h|--help) echo "$usage"; exit ;;
    *) echo "$usage" >&2; exit 2 ;;
  esac
  shift
done

"$python" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else "Python 3.12 is required")'
"$python" -m venv "$venv"
"$venv/bin/python" -m pip install -r "$module/requirements.txt" "$spark" "$module$extras"
"$venv/bin/python" -c 'import swarmx_planning.graph_io; import spark_dsg'
printf '[Hydra-ACRL] Use %s/bin/python for the saved-DSG experiments.\n' "$venv"
