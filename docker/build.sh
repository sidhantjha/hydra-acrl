#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$root"
die() { printf '[Hydra-ACRL] %s\n' "$*" >&2; exit 1; }

# Called only in a Docker build stage. Colcon owns ordering and dependency failures.
if [[ ${1:-} == _compile ]]; then
  workspace=$2
  export MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1 PYTHONUNBUFFERED=1
  set +u
  source /opt/ros/jazzy/setup.bash
  expected=22 offset=0
  args=(--cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF)
  case "$workspace" in
    hydra_ws) export COLCON_DEFAULTS_FILE="$root/hydra_mapping/hydra_ws/colcon_defaults.yaml" ;;
    tb3_ws)
      source hydra_mapping/hydra_ws/install/local_setup.bash
      expected=1 offset=22 args=()
      ;;
    *) die "Unknown build workspace: $workspace." ;;
  esac
  set -u
  cd "$root/hydra_mapping/$workspace"
  packages=$(colcon list --base-paths src --topological-order --names-only)
  [[ -n "$packages" && $(wc -l <<< "$packages") -eq "$expected" ]] ||
    die "Expected $expected packages in $workspace. Colcon found: $packages"
  printf '[Hydra-ACRL] Colcon dependency order for %s\n%s\n' "$workspace" "$packages"
  colcon build --base-paths src --executor sequential --event-handlers console_direct+ "${args[@]}" 2>&1 |
    awk -v offset="$offset" '
      /^Starting >>> / { i[$3]=++offset; printf "[%02d/23] Building %s\n", i[$3], $3; fflush(); next }
      /^Finished <<< / { printf "[%02d/23] Finished %s\n", i[$3], $3; fflush(); next }
      { print; fflush() }
    '
  exit
fi

usage='Usage: bash docker/build.sh [--planning-only|--help]
Build the local mapping image with both requested tags. The NVIDIA CUDA 12.6
runtime check runs first. --planning-only builds hydra-acrl:planning without GPU.'
case "${1:-}" in
  -h|--help) printf '%s\n' "$usage"; exit ;;
  ''|--planning-only) [[ $# -le 1 ]] || die "$usage" ;;
  *) die "$usage" ;;
esac
command -v docker >/dev/null || die "Install Docker Engine or Docker Desktop with WSL integration."
docker info --format '[Hydra-ACRL] Docker {{.ServerVersion}}, CPUs {{.NCPU}}, memory {{.MemTotal}} bytes, data root {{.DockerRootDir}}' ||
  die "Docker is not running or this shell cannot access it."
docker buildx version
[[ $(docker info --format '{{.Architecture}}') == x86_64 ]] || die "This release targets an amd64 Docker host."
docker system df
echo '[Hydra-ACRL] BuildKit cache summary'
docker buildx du | tail -n 4
echo '[Hydra-ACRL] Host storage and memory'
df -h "$root"
if mountpoint -q /mnt/c; then df -h /mnt/c; fi
free -h

target=mapping
probe=nvidia/cuda:12.6.3-base-ubuntu24.04@sha256:6b3201183858bad08441837f5a5efc2c75290135cc25fcc87d9ff763190cfd09
minimum_gib=30
if [[ ${1:-} == --planning-only ]]; then
  target=planning
  probe=ubuntu:24.04@sha256:9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a
  minimum_gib=5
fi
echo "[Hydra-ACRL] Inspect Docker filesystem capacity for $target"
available_kib=$(docker run --rm --pull missing --entrypoint df "$probe" -Pk / | awk 'NR == 2 { print $4 }')
[[ "$available_kib" =~ ^[0-9]+$ ]] || die "Could not measure available Docker storage."
printf '[Hydra-ACRL] Docker filesystem free: %d GiB\n' "$((available_kib / 1048576))"
(( available_kib >= minimum_gib * 1048576 )) ||
  die "Insufficient Docker storage. Allow at least $minimum_gib GiB free for this build."
# Docker Desktop's sparse disk also depends on free space on its Windows filesystem.
if mountpoint -q /mnt/c; then
  windows_kib=$(df -Pk /mnt/c | awk 'NR == 2 { print $4 }')
  if (( windows_kib < minimum_gib * 1048576 )); then
    printf '[Hydra-ACRL] Windows C: has less than %d GiB free. Check where Docker Desktop stores its virtual disk.\n' "$minimum_gib" >&2
  fi
fi

build=(docker buildx build --platform linux/amd64 --progress=plain --load --target "$target")
if [[ "$target" == planning ]]; then
  exec "${build[@]}" -t hydra-acrl:planning .
fi

echo '[Hydra-ACRL] Check NVIDIA GPU passthrough and the CUDA 12.6 image requirement'
docker run --rm --pull missing --gpus all "$probe" nvidia-smi ||
  die "CUDA 12.6 GPU preflight failed. Check Docker's NVIDIA support and the host driver. The mapping build was skipped."
bash hydra_mapping/scripts/prepare_external.sh aws
exec "${build[@]}" -t hydra-acrl:latest -t hydra-acrl:1.0.0 .
