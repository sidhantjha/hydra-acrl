#!/usr/bin/env bash
set -euo pipefail
root=/opt/hydra-acrl
die() { printf '[Hydra-ACRL] %s\n' "$*" >&2; exit 1; }
mkdir -p -- "$HOME"

if [[ ${1:-} == planning ]]; then
  shift
  export PATH="$root/hydra_task_and_motion_planning/.venv/bin:$PATH" MPLBACKEND=Agg
  cd "$root/hydra_task_and_motion_planning"
  exec "$@"
fi
if [[ ${1:-} != dashboard ]]; then
  exec "$@"
fi
shift
cd "$root"

[[ -s /assets/model.onnx ]] || die "Mount the authorized EfficientViT ONNX model."
[[ -d /assets/engine && -w /assets/engine ]] || die "Mount a writable TensorRT engine cache."
exec 9>/assets/engine/.engine.lock
flock -n 9 || die "This engine cache is in use. Use a separate HYDRA_ACRL_STATE_DIR."
model_dir=$(mktemp -d)
ln -s /assets/model.onnx "$model_dir/ade20k-efficientvit_seg_l2.onnx"
ln -s /assets/engine/ade20k-efficientvit_seg_l2.trt "$model_dir/ade20k-efficientvit_seg_l2.trt"
export SEMANTIC_INFERENCE_MODEL_DIR="$model_dir"
if [[ ${HYDRA_ACRL_WSLG:-0} == 1 ]]; then
  export LD_LIBRARY_PATH="/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
if [[ -n ${DISPLAY:-} ]]; then
  gl=$(timeout 15s glxinfo -B) ||
    die "Container OpenGL could not open DISPLAY=$DISPLAY. Check the socket, Xauthority and graphics driver."
  grep -E '^OpenGL (renderer string|core profile version string|version string):' <<< "$gl"
fi
dashboard=$(./launch.sh "$@" </dev/null)
printf '%s\n' "$dashboard"
session=$(awk '/^Stop: / {print $NF}' <<< "$dashboard")
[[ -n "$session" ]] || die "The mapping launcher did not return a dashboard session."
tm() { tmux -L "$session" "$@"; }
backend=$(tm list-panes -t "$session" -F '#{pane_id}' | sed -n '1p')
printf 'From the host: docker exec -it %s ./launch.sh stop %s\n' "${HYDRA_ACRL_CONTAINER:-CONTAINER}" "$session"
printf 'From the host: docker exec -it %s tmux -L %s attach -t %s\n' "${HYDRA_ACRL_CONTAINER:-CONTAINER}" "$session" "$session"
request_stop() {
  ./launch.sh stop "$session" || true
  tm detach-client -s "$session" 2>/dev/null || true
}
trap request_stop INT TERM HUP

if [[ -t 0 && -t 1 ]]; then
  tm attach -t "$session" <&0 &
  wait "$!" || true
fi
while [[ $(tm display-message -p -t "$backend" '#{pane_dead}') == 0 ]]; do
  sleep 1 &
  wait "$!" || true
done
tm capture-pane -p -t "$backend" -S -35
exit "$(tm display-message -p -t "$backend" '#{pane_dead_status}')"
