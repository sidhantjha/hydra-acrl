#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
mapping="$root/hydra_mapping"
assets="$mapping/small_house"
source "$mapping/scripts/mapping_environment.sh"

usage() {
  cat <<'EOF'
Hydra-ACRL Small House dashboard
Usage: ./launch.sh [--headless] [--no-rviz] [--reuse-engine|--rebuild-engine]
       ./launch.sh stop SESSION
       ./launch.sh --help

--headless        Skip Gazebo GUI and RViz. Keep teleoperation and streaming.
--no-rviz         Skip RViz. Keep the Gazebo GUI and streaming visualizer.
--reuse-engine    Use an existing compatible TensorRT engine.
--rebuild-engine  Regenerate the TensorRT engine beside the ONNX file.
--help            Show this message.

An existing engine requires an explicit choice. ROS_DOMAIN_ID defaults to 42.
The dashboard starts detached when called without a terminal. F3 selects teleop.
Use the stop command or Ctrl+C in Mapping backend to stop and export.
EOF
}

status() { printf '[Hydra-ACRL] %s\n' "$*"; }
tm() { tmux -L "$session" "$@"; }

ros_info() {
  timeout -k 2s 9s ros2 topic info --no-daemon --spin-time 3 "$@"
}

ros_sample() {
  local stamp
  stamp=$(timeout -k 2s 8s ros2 topic echo "$1" "$2" --no-daemon --spin-time 0 \
    --once --timeout 5 --qos-reliability best_effort --qos-durability volatile --field header.stamp) || return
  printf '%s\n' "$stamp"
  # Jazzy can exit 0 on an echo timeout. Require a received message.
  grep -Eq '^sec: -?[0-9]+$' <<< "$stamp"
}

robot_ready() {
  timeout -k 2s 15s gz model --list | awk '$1 == "-" && $2 == "hydra_waffle" {found=1} END {exit !found}'
}

bridge_ready() {
  local info
  info=$(ros_info /cmd_vel) && printf '%s\n' "$info" &&
    grep -Fxq "Type: geometry_msgs/msg/TwistStamped" <<< "$info" &&
    grep -Fxq "Subscription count: 1" <<< "$info" &&
    grep -Fxq "Publisher count: 0" <<< "$info" &&
    timeout -k 2s 5s gz topic -i -t /cmd_vel | awk '
      /Subscribers/ { subscribers=1 }
      subscribers && /gz.msgs.Twist/ { found=1 }
      END { exit !found }
    '
}

teleop_ready() {
  local info
  info=$(ros_info /cmd_vel --verbose) && printf '%s\n' "$info" &&
    grep -Fxq "Publisher count: 1" <<< "$info" &&
    grep -Fxq "Node name: teleop_twist_keyboard" <<< "$info"
}

visualizer_ready() {
  local info
  info=$(ros_info /hydra/backend/dsg --verbose) && printf '%s\n' "$info" &&
    grep -Fxq "Node name: hydra_visualizer" <<< "$info"
}

await_stage() {
  local seconds=$1 label=$2 deadline
  shift 2
  deadline=$((SECONDS + seconds))
  status "Waiting for $label (up to ${seconds}s)."
  while (( SECONDS < deadline )); do
    [[ ! -e "$run/stop" ]] || return 1
    if ! kill -0 "$backend_pid" 2>/dev/null; then
      status "Mapping exited while waiting for $label. See the Mapping backend log."
      return 1
    fi
    printf '\n%s: %s\n' "$(date -u +%FT%TZ)" "$label" >> "$run/readiness.log"
    if "$@" >>"$run/readiness.log" 2>&1; then
      status "Ready: $label."
      return 0
    fi
    sleep 1
  done
  status "Timed out waiting for $label. See the pane logs and $run/readiness.log."
  return 1
}

pane_alive() { [[ $(tm display-message -p -t "$1" '#{pane_dead}' 2>/dev/null) == 0 ]]; }

interrupt_pane() {
  local pane=$1
  if pane_alive "$pane"; then
    tm send-keys -t "$pane" C-c
  fi
}

wait_auxiliaries() {
  local deadline=$((SECONDS + 15)) pane
  for pane in "$@"; do
    while pane_alive "$pane" && (( SECONDS < deadline )); do sleep 0.2; done
    if pane_alive "$pane"; then
      status "Auxiliary pane $pane is still running after SIGINT. Sending SIGTERM."
      local pid
      pid=$(tm display-message -p -t "$pane" '#{pane_pid}')
      kill -TERM -- "-$pid" 2>/dev/null || true
      local term_deadline=$((SECONDS + 5))
      while pane_alive "$pane" && (( SECONDS < term_deadline )); do sleep 0.2; done
      if pane_alive "$pane"; then
        status "Auxiliary pane $pane did not close after SIGTERM. Stopping its process group."
        kill -KILL -- "-$pid" 2>/dev/null || true
      fi
    fi
  done
}

startup() {
  await_stage 90 "Gazebo entity hydra_waffle" robot_ready || return 1
  : > "$run/start-gui"
  await_stage 45 "stamped velocity bridge and Gazebo drive subscriber" bridge_ready || return 1
  await_stage 45 "odometry messages" ros_sample /odom nav_msgs/msg/Odometry || return 1
  : > "$run/start-teleop"
  await_stage 30 "keyboard teleoperation publisher (F3 to drive)" teleop_ready || return 1
  : > "$run/start-visualizer"
  await_stage 45 "Hydra visualizer subscription on /hydra/backend/dsg" visualizer_ready || return 1
  await_stage 600 "real semantic frames (an engine build can take several minutes)" \
    ros_sample /tesse/left_cam/semantic/image_raw sensor_msgs/msg/Image || return 1
  await_stage 90 "live backend scene graph messages" \
    ros_sample /hydra/backend/dsg hydra_msgs/msg/DsgUpdate || return 1
}

backend() {
  local gui_pane=$1 teleop_pane=$2 visualizer_pane=$3 rc=0 startup_rc=0 existing
  # Hold the lease in this pane until mapping and export both finish.
  exec 9>"$mapping/runs/.ros-domain-$ROS_DOMAIN_ID.lock"
  if ! flock -n 9; then
    : > "$run/stop"
    die "ROS domain $ROS_DOMAIN_ID is in use by another Hydra-ACRL dashboard. Choose another domain."
  fi
  trap ': > "$run/stop"' EXIT INT TERM HUP
  existing=$(timeout -k 2s 8s ros2 node list --no-daemon --spin-time 2) ||
    die "ROS discovery failed in domain $ROS_DOMAIN_ID. Check DDS access and ROS setup."
  [[ -z "$existing" ]] || die "ROS domain $ROS_DOMAIN_ID already contains nodes. Choose an unused ROS_DOMAIN_ID."
  [[ ! -e "$run/stop" ]] || return 0
  # Give the ROS launch its own process group and keep SIGINT enabled for this job.
  set -m
  status "Starting headless mapping server (ROS domain $ROS_DOMAIN_ID, Gazebo partition $GZ_PARTITION)."
  "$mapping/scripts/run_mapping.sh" --run-dir "$run/mapping" ${engine:+"$engine"} 9>&- &
  backend_pid=$!
  if startup; then
    status "Mapping is live. F3 selects teleop. Stop with ./launch.sh stop $session."
    while [[ ! -e "$run/stop" ]] && kill -0 "$backend_pid" 2>/dev/null; do sleep 1; done
  elif [[ ! -e "$run/stop" ]]; then
    startup_rc=1
    status "Startup failed. Closing this run's processes and preserving the dashboard."
  fi

  : > "$run/stop"
  # Leaving teleop also publishes zero. Publish an explicit zero before stopping the bridge.
  interrupt_pane "$teleop_pane"
  if [[ -e "$run/start-teleop" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    wait_auxiliaries "$teleop_pane"
    if ! timeout -k 2s 8s ros2 topic pub --once -w 1 /cmd_vel geometry_msgs/msg/TwistStamped \
      '{header: auto, twist: {linear: {x: 0.0}, angular: {z: 0.0}}}'; then
      status "Could not confirm delivery of the final zero velocity to the bridge."
    fi
  fi
  interrupt_pane "$gui_pane"
  interrupt_pane "$visualizer_pane"
  if kill -0 "$backend_pid" 2>/dev/null; then
    status "Stopping mapping. Allow up to 180 seconds for Hydra to save before ROS escalation."
    # ROS launch treats SIGINT like terminal Ctrl+C, so deliver it to its child group.
    kill -INT -- "-$backend_pid" 2>/dev/null || true
  fi
  # A repeated stop request may interrupt wait. Keep waiting for the same child.
  while true; do
    rc=0
    wait "$backend_pid" || rc=$?
    kill -0 "$backend_pid" 2>/dev/null || break
  done
  wait_auxiliaries "$gui_pane" "$visualizer_pane"
  if [[ -f "$run/mapping/hydra_exit.json" ]]; then
    if "$mapping/scripts/export_dsg.sh" "$run/mapping" "$run/dsg.json"; then
      status "DSG and export report saved in $run."
    else
      status "No DSG exported. Review Hydra's exit record and backend files in $run/mapping."
      rc=1
    fi
  else
    status "No Hydra exit record. See $run/mapping-backend.log."
    rc=1
  fi
  (( rc == 0 )) || return "$rc"
  return "$startup_rc"
}

auxiliary() {
  local component=$1
  case "$component" in
    gui)
      if [[ "$headless" == true ]]; then status "Gazebo GUI disabled."; return; fi ;;
    visualizer)
      if [[ "$rviz" == false ]]; then status "RViz disabled. Streaming visualizer remains enabled."; fi ;;
  esac
  status "Waiting for the mapping backend to release $component."
  while [[ ! -e "$run/start-$component" && ! -e "$run/stop" ]]; do sleep 0.2; done
  [[ ! -e "$run/stop" ]] || return 0
  case "$component" in
    gui)
      local tb3 robotis
      tb3=$(ros2 pkg prefix --share tb3_hydra_bringup)
      robotis=$(ros2 pkg prefix --share turtlebot3_gazebo)
      export GZ_SIM_RESOURCE_PATH="$tb3/models:$assets/models:$robotis/models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
      status "Attaching Gazebo GUI after robot spawn."
      exec gz sim -g ;;
    teleop)
      [[ -t 0 ]] || die "Teleoperation requires an interactive terminal."
      status "Keyboard teleoperation active. Focus this pane with F3."
      exec ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true ;;
    visualizer)
      mkdir -p "$run/visualizer-ros-logs"
      export ROS_LOG_DIR="$run/visualizer-ros-logs"
      status "Starting Hydra streaming visualizer (start_rviz=$rviz)."
      exec ros2 launch tb3_hydra_bringup small_house_visualizer.launch.py "start_rviz:=$rviz" ;;
  esac
}

# tmux invokes each pane with the launcher environment captured by its own server.
if [[ ${1:-} == _pane ]]; then
  component=$2
  run=$3
  session=${run##*/}
  [[ -n ${TMUX_PANE:-} && -d "$run" && $session == hydra-acrl-* ]] || die "Invalid dashboard pane."
  while [[ ! -e "$run/dashboard-ready" && ! -e "$run/stop" ]]; do sleep 0.1; done
  [[ ! -e "$run/stop" ]] || exit 0
  if [[ "$component" == backend ]]; then
    read -r gui_pane teleop_pane visualizer_pane < "$run/dashboard-ready"
    backend "$gui_pane" "$teleop_pane" "$visualizer_pane"
  else
    auxiliary "$component"
  fi
  exit
fi

if [[ ${1:-} == stop ]]; then
  [[ $# == 2 && "$2" =~ ^hydra-acrl-[0-9]{8}T[0-9]{6}Z-[[:alnum:]]{8}$ ]] || die "Usage: ./launch.sh stop SESSION"
  session=$2
  run="$mapping/runs/$session"
  [[ -f "$run/dashboard-ready" ]] && tm has-session -t "=$session" 2>/dev/null ||
    die "No Hydra-ACRL dashboard named $session in this checkout."
  backend_pane=$(tm list-panes -t "$session" -F '#{pane_id}' | head -n1)
  if ! pane_alive "$backend_pane"; then
    status "Mapping has already stopped. Review $run/mapping-backend.log."
    exit
  fi
  : > "$run/stop"
  status "Stop requested for $session. Watch $run/mapping-backend.log for shutdown and export."
  exit
fi

headless=false
rviz=true
engine=''
while (( $# )); do
  case "$1" in
    --headless) headless=true ;;
    --no-rviz) rviz=false ;;
    --reuse-engine|--rebuild-engine) [[ -z "$engine" ]] || die "Choose one TensorRT engine option."; engine=$1 ;;
    -h|--help) usage; exit ;;
    *) die "Unknown option: $1. See ./launch.sh --help." ;;
  esac
  shift
done
if [[ "$headless" == true ]]; then rviz=false; fi
for tool in tmux timeout; do command -v "$tool" >/dev/null || die "Install $tool."; done
check_engine
check_assets
if [[ "$headless" == false && -z ${DISPLAY:-}${WAYLAND_DISPLAY:-} ]]; then
  die "No graphical display. Start from a desktop terminal or use --headless."
fi
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"
[[ "$ROS_DOMAIN_ID" =~ ^(0|[1-9][0-9]{0,2})$ ]] && (( ROS_DOMAIN_ID <= 232 )) ||
  die "ROS_DOMAIN_ID must be an integer from 0 to 232."
export ROS_AUTOMATIC_DISCOVERY_RANGE="${ROS_AUTOMATIC_DISCOVERY_RANGE:-LOCALHOST}"
source_mapping_ros
configure_mapping_runtime
ros2 pkg prefix teleop_twist_keyboard >/dev/null || die "Install ros-jazzy-teleop-twist-keyboard."
ros2 pkg prefix hydra_visualizer >/dev/null || die "Build the release Hydra visualizer overlay."
if [[ "$rviz" == true ]]; then
  ros2 pkg prefix rviz2 >/dev/null || die "Install ros-jazzy-rviz2 or use --no-rviz."
fi

mkdir -p "$mapping/runs"
run=$(mktemp -d "$mapping/runs/hydra-acrl-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXXXX")
session=${run##*/}
# Use an isolated Gazebo transport partition and give each dashboard its own tmux server.
export GZ_PARTITION="$session" headless rviz engine
export LC_ALL=C.UTF-8
trap ': > "$run/stop"; tm kill-session -t "=$session" 2>/dev/null || true' EXIT
backend_pane=$(tm -f /dev/null new-session -d -x 140 -y 42 -s "$session" -n "Hydra-ACRL" \
  -c "$run" -P -F '#{pane_id}' "$root/launch.sh" _pane backend "$run")
tm set-option -t "$session" remain-on-exit on
tm set-option -t "$session" pane-border-status top
tm set-option -t "$session" pane-border-format ' #{pane_title} #{?pane_dead,[exited #{pane_dead_status}],} '
tm set-option -t "$session" mouse on
gui_pane=$(tm split-window -h -t "$backend_pane" -c "$run" -P -F '#{pane_id}' "$root/launch.sh" _pane gui "$run")
teleop_pane=$(tm split-window -v -t "$backend_pane" -c "$run" -P -F '#{pane_id}' "$root/launch.sh" _pane teleop "$run")
visualizer_pane=$(tm split-window -v -t "$gui_pane" -c "$run" -P -F '#{pane_id}' "$root/launch.sh" _pane visualizer "$run")
tm select-layout -t "$session" tiled >/dev/null
tm bind-key -n F3 select-pane -t "$teleop_pane"
tm select-pane -t "$backend_pane" -T 'Mapping backend'
tm select-pane -t "$gui_pane" -T 'Gazebo GUI'
tm select-pane -t "$teleop_pane" -T 'Manual keyboard teleoperation (F3)'
tm select-pane -t "$visualizer_pane" -T 'Hydra visualizer and RViz'
for pane_log in "$backend_pane:mapping-backend" "$gui_pane:gazebo-gui" \
  "$teleop_pane:teleoperation" "$visualizer_pane:visualizer"; do
  printf -v log_command 'cat >> %q' "$run/${pane_log#*:}.log"
  tm pipe-pane -t "${pane_log%%:*}" "$log_command"
done
tm select-pane -t "$backend_pane"
printf '%s %s %s\n' "$gui_pane" "$teleop_pane" "$visualizer_pane" > "$run/panes"
mv -- "$run/panes" "$run/dashboard-ready"
trap - EXIT
status "Dashboard $session. Logs and results: $run"
printf 'Attach: tmux -L %s attach -t %s\nStop:   ./launch.sh stop %s\n' "$session" "$session" "$session"
if [[ -t 0 && -t 1 ]]; then
  exec env -u TMUX tmux -L "$session" attach -t "$session"
fi
