#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
mapping="$root/hydra_mapping"
source "$mapping/scripts/mapping_environment.sh"
usage() {
  cat <<'HELP'
Hydra-ACRL container launcher

  bash docker/run.sh [--headless] [--no-rviz] [--reuse-engine|--rebuild-engine]
  bash docker/run.sh --planning COMMAND [ARG ...]
  bash docker/run.sh --help

Run the four-pane mapping dashboard in a local CUDA 12.6 image, or use CPU
planning after bash docker/build.sh --planning-only. With --headless, the
simulator keeps rendering sensors. HYDRA_ACRL_RENDER auto uses X11 when DISPLAY
is set and EGL otherwise. Set it to egl to test display-free headless rendering.

HYDRA_ACRL_ONNX       path to authorized model (default: native model cache)
HYDRA_ACRL_AWS        path to prepared AWS Small House directory
HYDRA_ACRL_STATE_DIR  directory for runs, engine, input and results (docker-data)
HYDRA_ACRL_REFERENCE  optional authorized run_01 directory for regression tests
HYDRA_ACRL_IMAGE      local mapping tag (default: hydra-acrl:latest)
HELP
}
if [[ ${1:-} == --help || ${1:-} == -h ]]; then usage; exit; fi

service=mapping
headless=false
engine=''
if [[ ${1:-} == --planning ]]; then
  service=planning
  shift
  if (( ! $# )); then set -- bash; fi
else
  for arg in "$@"; do
    case "$arg" in
      --headless) headless=true ;;
      --no-rviz) ;;
      --reuse-engine|--rebuild-engine)
        [[ -z "$engine" ]] || die "Choose one TensorRT engine option."
        engine=$arg
        ;;
      *) die "Unknown option: $arg. See bash docker/run.sh --help." ;;
    esac
  done
fi
command -v docker >/dev/null || die "Install Docker Engine or Docker Desktop with WSL integration."
docker info >/dev/null 2>&1 || die "Docker is not running or this shell cannot access it."
docker compose version >/dev/null || die "Install the Docker Compose plugin."
export HYDRA_ACRL_STATE_DIR
HYDRA_ACRL_STATE_DIR=$(realpath -m -- "${HYDRA_ACRL_STATE_DIR:-"$root/docker-data"}")
export HYDRA_ACRL_UID=$(id -u) HYDRA_ACRL_GID=$(id -g)
compose=(docker compose --project-directory "$root" -f "$root/compose.yaml")
options=(--rm --no-deps --pull never)
if [[ ! -t 0 || ! -t 1 ]]; then options+=(-T); fi
mkdir -p "$HYDRA_ACRL_STATE_DIR"/{input,results}
[[ -w "$HYDRA_ACRL_STATE_DIR/results" ]] || die "Planning results directory is not writable."

if [[ -n ${HYDRA_ACRL_REFERENCE:-} ]]; then
  reference=$(realpath -- "$HYDRA_ACRL_REFERENCE") || die "Reference DSG directory does not exist."
  [[ -r "$reference/dsg.json" ]] || die "HYDRA_ACRL_REFERENCE must contain a readable dsg.json."
  options+=(-v "$reference:/opt/hydra-acrl/hydra_task_and_motion_planning/experiments/small_house/run_01:ro")
fi
if [[ "$service" == planning ]]; then
  docker image inspect hydra-acrl:planning >/dev/null 2>&1 ||
    die "Build the CPU planning image with bash docker/build.sh --planning-only."
  exec "${compose[@]}" run "${options[@]}" planning "$@"
fi

export HYDRA_ACRL_ONNX=${HYDRA_ACRL_ONNX:-"$root/hydra_mapping/external/models/ade20k-efficientvit_seg_l2.onnx"}
export HYDRA_ACRL_AWS=${HYDRA_ACRL_AWS:-"$root/hydra_mapping/small_house"}
export HYDRA_ACRL_IMAGE=${HYDRA_ACRL_IMAGE:-hydra-acrl:latest}
[[ -s "$HYDRA_ACRL_ONNX" && -r "$HYDRA_ACRL_ONNX" ]] ||
  die "Place an authorized ade20k-efficientvit_seg_l2.onnx at $HYDRA_ACRL_ONNX."
[[ -d "$HYDRA_ACRL_AWS/models" && -s "$HYDRA_ACRL_AWS/.source-revision" &&
   $(<"$HYDRA_ACRL_AWS/.source-revision") == ff9631ca6d1db9c1ba656498151464b5ab74aafe &&
   -f "$HYDRA_ACRL_AWS/.portrait-textures" ]] ||
  die "Prepare the pinned AWS Small House assets with hydra_mapping/scripts/prepare_external.sh aws or set HYDRA_ACRL_AWS."
HYDRA_ACRL_ONNX=$(realpath -- "$HYDRA_ACRL_ONNX")
HYDRA_ACRL_AWS=$(realpath -- "$HYDRA_ACRL_AWS")
mkdir -p "$HYDRA_ACRL_STATE_DIR"/{engine,runs}
[[ -w "$HYDRA_ACRL_STATE_DIR/engine" && -w "$HYDRA_ACRL_STATE_DIR/runs" ]] ||
  die "Mapping runs and engine cache must be writable by your user."
if [[ -z "$engine" ]]; then
  choose_engine "$HYDRA_ACRL_STATE_DIR/engine/ade20k-efficientvit_seg_l2.trt"
  if [[ -n "$engine" ]]; then set -- "$@" "$engine"; fi
fi

render=${HYDRA_ACRL_RENDER:-auto}
if [[ "$render" == auto ]]; then
  render=x11
  if [[ "$headless" == true && -z ${DISPLAY:-} ]]; then render=egl; fi
fi
case "$render" in
  egl)
    [[ "$headless" == true ]] || die "Use --headless with HYDRA_ACRL_RENDER=egl."
    options+=(-e HYDRA_ACRL_EGL=1)
    ;;
  x11)
    [[ ${DISPLAY:-} =~ ^(unix)?:([0-9]+)(\.[0-9]+)?$ ]] ||
      die "A local X11 or WSLg DISPLAY is required. For offscreen rendering use --headless with HYDRA_ACRL_RENDER=egl."
    display_number=${BASH_REMATCH[2]}
    [[ -S "/tmp/.X11-unix/X$display_number" ]] ||
      die "Missing X11 socket for DISPLAY=$DISPLAY. Start WSLg or your local X server."
    socket_dir=$(realpath -- /tmp/.X11-unix)
    options+=(-e "DISPLAY=$DISPLAY" -e QT_QPA_PLATFORM=xcb -v "$socket_dir:/tmp/.X11-unix:ro")
    if [[ -S "/mnt/wslg/.X11-unix/X$display_number" && -c /dev/dxg ]]; then
      service=mapping-wslg
    fi
    source_auth=${XAUTHORITY:-"$HOME/.Xauthority"}
    cookie=''
    if [[ -r "$source_auth" ]] && command -v xauth >/dev/null; then
      cookie=$(xauth -f "$source_auth" nlist "$DISPLAY") || die "Could not read the Xauthority cookie for DISPLAY=$DISPLAY."
    fi
    if [[ -n "$cookie" ]]; then
      auth_file=$(mktemp)
      trap 'rm -f -- "$auth_file"' EXIT
      sed 's/^..../ffff/' <<< "$cookie" | xauth -f "$auth_file" nmerge -
      options+=(-e XAUTHORITY=/tmp/hydra-acrl.xauth -v "$auth_file:/tmp/hydra-acrl.xauth:ro")
    elif [[ "$service" != mapping-wslg ]]; then
      die "No Xauthority cookie for DISPLAY=$DISPLAY. Run from the local desktop with xauth and its session cookie."
    fi
    ;;
  *) die "HYDRA_ACRL_RENDER must be auto, x11 or egl." ;;
esac

docker image inspect "$HYDRA_ACRL_IMAGE" >/dev/null 2>&1 ||
  die "Missing local image $HYDRA_ACRL_IMAGE. Run bash docker/build.sh."
docker run --rm --pull never --gpus all --entrypoint nvidia-smi "$HYDRA_ACRL_IMAGE" -L ||
  die "NVIDIA GPU access or CUDA 12.6 compatibility failed. Check the host driver and Docker GPU setup."
name="hydra-acrl-$(date -u +%Y%m%dT%H%M%SZ)-$$"
printf '[Hydra-ACRL] Start %s with %s rendering.\n' "$name" "$render"
"${compose[@]}" run "${options[@]}" --name "$name" -e "HYDRA_ACRL_CONTAINER=$name" "$service" dashboard "$@"
