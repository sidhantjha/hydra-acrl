#!/usr/bin/env bash
set -euo pipefail
mapping=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$mapping/scripts/mapping_environment.sh"
usage='Usage: setup.sh [--check-only|--resume|--help]'
case "${1:-}" in
  ""|--check-only|--resume) [[ $# -le 1 ]] || die "$usage" ;;
  --help|-h) echo "$usage"; exit ;;
  *) die "$usage" ;;
esac
printf '%s\n' '[Hydra-ACRL] Stage 1/3: check mapping prerequisites.'
source /etc/os-release
[[ $ID == ubuntu && $VERSION_ID == 24.04 ]] || die "Expected Ubuntu 24.04."
[[ ${ROS_DISTRO:-jazzy} == jazzy ]] || die "Start in a shell without another ROS distribution."
source_ros "${ROS_JAZZY_SETUP:-/opt/ros/jazzy/setup.bash}"
[[ ${ROS_DISTRO:-} == jazzy ]] || die "Expected ROS 2 Jazzy."
for tool in colcon cmake c++ git python3 ros2 gz sha256sum flock; do
  command -v "$tool" >/dev/null || die "Install the required tool: $tool"
done
cuda_root=${CUDAToolkit_ROOT:-/usr/local/cuda}
if command -v nvcc >/dev/null; then
  nvcc --version | tail -1
  if [[ -z ${CUDAToolkit_ROOT:-} ]]; then
    cuda_root=$(dirname -- "$(dirname -- "$(realpath -- "$(command -v nvcc)")")")
  fi
else
  [[ -x "$cuda_root/bin/nvcc" ]] || die "Install a compatible CUDA development toolkit or set CUDAToolkit_ROOT."
  "$cuda_root/bin/nvcc" --version | tail -1
fi
multiarch=$(c++ -print-multiarch)
trt_root=${TensorRT_ROOT:-/usr}
trt_include="$trt_root/include"
[[ -r "$trt_include/NvInfer.h" ]] || trt_include="$trt_root/include/$multiarch"
[[ -r "$trt_include/NvInfer.h" && -r "$trt_include/NvInferVersion.h" ]] ||
  die "Install TensorRT development headers or set TensorRT_ROOT."
for lib in nvinfer nvinfer_plugin nvonnxparser; do
  [[ -r "$trt_root/lib/$multiarch/lib$lib.so" || -r "$trt_root/lib/lib$lib.so" ||
     -r "$trt_root/lib64/lib$lib.so" ]] || die "Missing TensorRT development library lib$lib.so."
done
grep -E '^#define NV_TENSORRT_(MAJOR|MINOR|PATCH) ' "$trt_include/NvInferVersion.h"
export CUDAToolkit_ROOT="$cuda_root" TensorRT_ROOT="$trt_root"
for pkg in turtlebot3_gazebo ros_gz_sim ros_gz_image ros_gz_bridge topic_tools cv_bridge; do
  ros2 pkg prefix "$pkg" >/dev/null || die "Missing ROS package: $pkg"
done
for dep in hydra hydra_ros spark_dsg semantic_inference config_utilities spatial_hash ianvs kimera_pgmo pose_graph_tools teaser_plusplus; do
  [[ -d "$mapping/hydra_ws/src/$dep" ]] || die "Missing vendored source: $dep"
done
tb3="$mapping/tb3_ws/src/tb3_hydra_bringup"
for resource in package.xml config/{bridge,hydra,hydra_input}.yaml worlds/small_house_hydra.world models/hydra_waffle/model.sdf; do
  [[ -s "$tb3/$resource" ]] || die "Missing TB3 resource: $resource"
done
if [[ ${1:-} != --check-only ]]; then
  "$mapping/scripts/prepare_external.sh" rpgo
  "$mapping/scripts/prepare_external.sh" aws
fi
assets="$mapping/small_house"
check_assets

if [[ ${1:-} == --check-only ]]; then
  [[ -s "$mapping/hydra_ws/src/kimera_rpgo/.source-revision" &&
     $(<"$mapping/hydra_ws/src/kimera_rpgo/.source-revision") == f1fee0900ef6825bf76304685668235cf5dd008d ]] ||
    die "Run hydra_mapping/setup.sh to fetch pinned Kimera-RPGO."
  check_model
  echo "Mapping preflight passed."
  exit
fi
if [[ -n ${SEMANTIC_INFERENCE_MODEL_DIR:-} || -e "$mapping/external/models/ade20k-efficientvit_seg_l2.onnx" ]]; then
  check_model
else
  echo "[Hydra-ACRL] Before launch, place an authorized ade20k-efficientvit_seg_l2.onnx in $mapping/external/models/."
fi
export MAKEFLAGS=-j1
export CMAKE_BUILD_PARALLEL_LEVEL=1
selection=()
if [[ ${1:-} == --resume ]]; then
  selection=(--packages-skip-build-finished)
fi

build_stage() (
  local stage=$1 workspace=$2
  shift 2
  cd "$mapping/$workspace"
  local packages
  packages=$(colcon list --base-paths src --topological-order --names-only) ||
    die "Package discovery failed in $workspace."
  echo "[Hydra-ACRL] Stage $stage/3: $workspace"
  [[ -n "$packages" ]] || die "No sources discovered in $workspace."
  printf '%s\n' "$packages" | nl -ba
  if (( ${#selection[@]} )); then
    echo "[Hydra-ACRL] Resuming packages without a successful colcon build record."
  fi
  echo "[Hydra-ACRL] Colcon reports progress in actual build order."
  if ! colcon build --base-paths src --executor sequential --event-handlers console_direct+ \
    "${selection[@]}" "$@"; then
    die "$workspace build failed. Inspect $mapping/$workspace/log/latest_build and use --resume after fixing the error."
  fi
)

export COLCON_DEFAULTS_FILE="$mapping/hydra_ws/colcon_defaults.yaml"
build_stage 2 hydra_ws --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
unset COLCON_DEFAULTS_FILE
source_ros "$mapping/hydra_ws/install/local_setup.bash"
build_stage 3 tb3_ws
echo "[Hydra-ACRL] Built both overlays. From the repository root, run ./launch.sh."
