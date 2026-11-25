#!/usr/bin/env bash
set -euo pipefail
mapping=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source "$mapping/scripts/mapping_environment.sh"
usage='Usage: run_mapping.sh [--run-dir NEW_DIRECTORY] [--gui] [--shutdown-grace SECONDS] [--reuse-engine|--rebuild-engine]'
run=''
gui=false
grace=180
engine=''
while (( $# )); do
  case "$1" in
    --run-dir) [[ $# -ge 2 ]] || die "$usage"; run=$2; shift ;;
    --shutdown-grace) [[ $# -ge 2 ]] || die "$usage"; grace=$2; shift ;;
    --gui) gui=true ;;
    --reuse-engine|--rebuild-engine) [[ -z "$engine" ]] || die "$usage"; engine=$1 ;;
    -h|--help) echo "$usage"; exit ;;
    *) die "$usage" ;;
  esac
  shift
done
[[ "$grace" =~ ^[1-9][0-9]*$ ]] || die "Shutdown grace must be a positive integer."
check_engine
assets="$mapping/small_house"
check_assets
source_mapping_ros
tb3=$(ros2 pkg prefix --share tb3_hydra_bringup)
hydra=$(ros2 pkg prefix --share hydra)
hydra_ros=$(ros2 pkg prefix --share hydra_ros)
semantic=$(ros2 pkg prefix --share semantic_inference_ros)
if [[ -z "$run" ]]; then
  mkdir -p "$mapping/runs"
  run=$(mktemp -d "$mapping/runs/small-house-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXXXX")
else
  mkdir -- "$run" || die "Choose a new run directory with an existing parent."
fi
run=$(cd -- "$run" && pwd -P)
mkdir "$run/config" "$run/ros_logs"
cp -- "$mapping/hydra.repos" "$run/config/"
cp -- "$tb3/config/"{bridge,hydra,hydra_input}.yaml "$run/config/"
cp -- "$hydra/config/label_spaces/ade20k_full_label_space.yaml" "$run/config/"
cp -- "$hydra/config/lcd/uhumans2.yaml" "$run/config/lcd.yaml"
cp -- "$hydra_ros/config/sinks/"{mesh_segmenter_sinks,gvd_places_sinks,active_window_sinks}.yaml "$run/config/"
cp -- "$semantic/config/models/ade20k-efficientvit_seg_l2.yaml" "$run/config/"
cp -- "$semantic/config/label_groupings/ade20k_full.yaml" "$run/config/semantic_labels.yaml"
cp -- "$tb3/launch/"{small_house_mapping,small_house_record_run,small_house_world,spawn_robot,hydra_interface_semantic,semantic_segmentation}.launch.py "$run/config/"
cp -- "$semantic/launch/closed_set.launch.yaml" "$run/config/"
cp -- "$semantic/config/distinct_150_colors.csv" "$run/config/"
sha256sum "$tb3/worlds/small_house_hydra.world" "$tb3/models/hydra_waffle/model.sdf" > "$run/config/sim_resources.sha256"
{
  printf 'started_utc=%s\n' "$(date -u +%FT%TZ)"
  printf 'ros_distro=%s\nros_domain_id=%s\n' "$ROS_DISTRO" "${ROS_DOMAIN_ID:-0}"
  printf 'gui=%s\nshutdown_grace_seconds=%s\nforce_rebuild=%s\n' "$gui" "$grace" "$force_rebuild"
  printf 'onnx_sha256=%s\naws_revision=%s\n' "$model_sha" "$(<"$assets/.source-revision")"
  if [[ "$engine" == --reuse-engine && -s "${model%.onnx}.trt" ]]; then
    engine_sha=$(sha256sum < "${model%.onnx}.trt")
    printf 'existing_engine_sha256=%s\n' "${engine_sha%% *}"
  fi
} > "$run/run_metadata.txt"
echo "[Hydra-ACRL] Mapping run: $run"
echo "Press Ctrl+C once and allow up to $grace seconds for Hydra to save."
export ROS_LOG_DIR="$run/ros_logs"
exec flock --exclusive --no-fork "$run/.mapping.lock" \
  ros2 launch tb3_hydra_bringup small_house_mapping.launch.py \
  "run_directory:=$run" "assets_models:=$assets/models" "gui:=$gui" \
  "shutdown_grace:=$grace" "force_rebuild:=$force_rebuild"
