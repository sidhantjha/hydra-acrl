# Sourced by setup and launchers, which define mapping.
die() { printf '[Hydra-ACRL] %s\n' "$*" >&2; exit 1; }

source_ros() {
  local script=$1
  [[ -r "$script" ]] || die "Missing ROS setup: $script"
  # ROS-generated setup hooks can read unset environment variables.
  set +u
  source "$script"
  set -u
}

check_model() {
  local expected=bce5de3bf3707258e7a2eff36b2f705595e6efcaeaab8e052f341057853a0072
  local model_dir=${SEMANTIC_INFERENCE_MODEL_DIR:-"$mapping/external/models"}
  [[ -s "$model_dir/ade20k-efficientvit_seg_l2.onnx" ]] ||
    die "Place an authorized ade20k-efficientvit_seg_l2.onnx in $model_dir/ (SHA256 $expected)."
  export SEMANTIC_INFERENCE_MODEL_DIR
  SEMANTIC_INFERENCE_MODEL_DIR=$(cd -- "$model_dir" && pwd -P)
  model="$SEMANTIC_INFERENCE_MODEL_DIR/ade20k-efficientvit_seg_l2.onnx"
  model_sha=$(sha256sum < "$model")
  model_sha=${model_sha%% *}
  [[ "$model_sha" == "$expected" || ${ALLOW_COMPATIBLE_MODEL:-0} == 1 ]] ||
    die "ONNX SHA256 differs from the historical model. Set ALLOW_COMPATIBLE_MODEL=1 only for an independently verified compatible export."
}

source_mapping_ros() {
  source_ros "${ROS_JAZZY_SETUP:-/opt/ros/jazzy/setup.bash}"
  source_ros "$mapping/hydra_ws/install/local_setup.bash"
  source_ros "$mapping/tb3_ws/install/local_setup.bash"
}

check_assets() {
  [[ -s "$assets/.source-revision" && -d "$assets/models" && -f "$assets/.portrait-textures" &&
     $(<"$assets/.source-revision") == ff9631ca6d1db9c1ba656498151464b5ab74aafe ]] ||
    die "Run hydra_mapping/setup.sh to restore the pinned Small House assets."
}

choose_engine() {
  [[ -e "$1" && -z "$engine" ]] || return 0
  [[ -t 0 && -t 1 ]] ||
    die "A TensorRT engine already exists. Choose --reuse-engine or --rebuild-engine."
  local choice
  read -rp "TensorRT engine exists. [u]se it or [r]ebuild it? " choice || die "TensorRT choice required."
  case "$choice" in
    u|U) engine=--reuse-engine ;;
    r|R) engine=--rebuild-engine ;;
    *) die "Choose --reuse-engine or --rebuild-engine." ;;
  esac
}

check_engine() {
  check_model
  choose_engine "${model%.onnx}.trt"
  force_rebuild=false
  if [[ "$engine" == --rebuild-engine ]]; then
    force_rebuild=true
  fi
  if [[ "$force_rebuild" == true || ! -s "${model%.onnx}.trt" ]]; then
    [[ -w "$SEMANTIC_INFERENCE_MODEL_DIR" ]] || die "TensorRT needs a writable model directory to generate its engine."
    [[ ! -e "${model%.onnx}.trt" || -w "${model%.onnx}.trt" ]] ||
      die "TensorRT engine is not writable: ${model%.onnx}.trt"
  fi
}

configure_mapping_runtime() {
  export CUDAToolkit_ROOT="${CUDAToolkit_ROOT:-/usr/local/cuda}"
  export TensorRT_ROOT="${TensorRT_ROOT:-/usr}"
  if [[ -d "$CUDAToolkit_ROOT/bin" ]]; then
    export PATH="$CUDAToolkit_ROOT/bin:$PATH"
  fi
  local lib
  for lib in "$CUDAToolkit_ROOT/lib64" "$TensorRT_ROOT/lib64" "$TensorRT_ROOT/lib"; do
    if [[ -d "$lib" ]]; then
      export LD_LIBRARY_PATH="$lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    fi
  done
  if [[ "$TensorRT_ROOT" != /usr ]]; then
    lib="$TensorRT_ROOT/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH)"
    if [[ -d "$lib" ]]; then
      export LD_LIBRARY_PATH="$lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    fi
  fi
}
