# Hydra-ACRL Docker guide

Run the commands from the repository root in a Linux terminal or an Ubuntu WSL2 terminal with Docker Desktop WSL integration. CPU planning requires Docker, BuildKit and Compose. The GPU and display requirements below apply to mapping. Docker handles ROS, Gazebo, CUDA, TensorRT, Python and the native build dependencies. The host needs Docker Engine or Docker Desktop with BuildKit and Compose, a CUDA-capable NVIDIA GPU, and a driver accepted by the pinned CUDA 12.6 image. Native Linux also needs NVIDIA Container Toolkit configured for Docker. A local X11/XWayland session is needed for desktop mode. Native Linux X11 requires the session’s Xauthority cookie and `xauth`.

**Current mapping build status.** The RTX 4080 passed Docker GPU passthrough. The pinned CUDA 12.6.3 base rejected Windows driver 551.95 with `unsatisfied condition: cuda>=12.6`. NVIDIA lists 561.17 or newer for the corresponding Windows toolkit driver, and 560.35.05 or newer on Linux. After installing a compatible driver yourself, rerun the preflight in the build command. CPU planning is available independently. [CUDA 12.6.3 release notes](https://docs.nvidia.com/cuda/archive/12.6.3/cuda-toolkit-release-notes/index.html)

### Build and prepare local inputs

The [Dockerfile](../Dockerfile) targets Ubuntu 24.04 amd64, ROS 2 Jazzy with its Gazebo Harmonic vendor packages, CUDA 12.6.3, TensorRT 10.4.0.26, Python 3.12 and Spark-DSG 1.1.3. [build.sh](../docker/build.sh) reports storage, RAM, swap, caches and the CUDA probe before starting mapping compilation. Allow about 30 GiB free on Docker’s backing filesystem. Build logs use plain progress and report packages in colcon dependency order. The system, TensorRT, ROS, Hydra overlay, bringup overlay and Python stages have reusable BuildKit layers. Use the same command to resume a build.

The build fetches the pinned Kimera-RPGO revision in the local mapping build stage and compiles both overlays. The robot, bridge and world configuration are in the checkout. Compose mounts the bundled Small House assets. Supply the ONNX once as described in the [quick start](../README.md#install-native-mapping).

```bash
bash docker/build.sh
```

The local mapping tags are `hydra-acrl:latest` and `hydra-acrl:1.0.0`. The image contains compiled Kimera-RPGO and is intended for local use. Build the verified standalone CPU target with `bash docker/build.sh --planning-only`.

### Run, control and stop

```bash
bash docker/run.sh
bash docker/run.sh --headless
```

[run.sh](../docker/run.sh) uses [compose.yaml](../compose.yaml) and starts the same [launch.sh](../launch.sh) dashboard. Press **F3** to focus teleoperation and **Ctrl+C** in the mapping pane for graceful stop. **Ctrl+B**, then **D**, detaches the dashboard while the container continues. The container prints the `docker exec` commands to reattach or stop the session from the host. Wait for the export summary before closing the dashboard.

WSLg desktop mode forwards its XWayland socket, `/dev/dxg` and read-only WSL graphics libraries and requests Mesa’s D3D12 NVIDIA adapter. Native Linux forwards the local X socket and a temporary copy of the session cookie. The container prints its OpenGL renderer before display-based startup. If X is available, `--headless` keeps X-based sensor rendering and skips the Gazebo and RViz windows. With no display, it requests Gazebo’s Ogre2 EGL path. To select that explicitly, use `HYDRA_ACRL_RENDER=egl bash docker/run.sh --headless --reuse-engine`. A separate ROS Jazzy container reached hardware OpenGL 4.6 and opened Gazebo and RViz windows through WSLg. The CUDA mapping dashboard and EGL sensor rendering remain unverified. [Microsoft WSLg container guide](https://github.com/microsoft/wslg/blob/main/samples/container/Containers.md), [Gazebo Harmonic EGL rendering](https://gazebosim.org/api/sim/8/headless_rendering.html)

| Host path | Container use |
| --- | --- |
| `HYDRA_ACRL_ONNX` | Read-only EfficientViT ONNX input |
| `HYDRA_ACRL_AWS` or `hydra_mapping/small_house/` | Read-only pinned AWS resources |
| `docker-data/engine/` | Writable hardware-specific TensorRT cache |
| `docker-data/runs/` | Console and ROS logs, raw graphs, meshes and validated `SESSION/dsg.json` |
| `docker-data/input/` | Read-only input DSGs under `/input` |
| `docker-data/results/` | Planning outputs under `/results` |

Use `HYDRA_ACRL_STATE_DIR` for a different location. The container runs as your numeric UID and GID. With an empty engine cache, TensorRT builds an engine at runtime. The launcher prompts for an existing engine. Use `--reuse-engine` or `--rebuild-engine` for noninteractive runs. Keep separate state directories for differing GPU, driver or TensorRT environments.

### Inspect or reproduce a saved graph in Docker

```bash
bash docker/build.sh --planning-only
mkdir -p docker-data/input
cp /absolute/path/to/dsg.json docker-data/input/
bash docker/run.sh --planning python scripts/inspect_small_house.py --dsg /input/dsg.json
# Use a new result directory and endpoint IDs from the selected graph.
bash docker/run.sh --planning python scripts/sweep_uncertainty.py --dsg /input/dsg.json

HYDRA_ACRL_REFERENCE="$PWD/hydra_task_and_motion_planning/experiments/small_house/run_01" \
  bash docker/run.sh --planning python -B -I -m unittest discover -s tests -v
```

Set `HYDRA_ACRL_REFERENCE` only when you have the authorized reference fixture. Copy a dashboard export into `docker-data/input/` to use the same commands.

### Docker troubleshooting

| Symptom | Check |
| --- | --- |
| Docker daemon unavailable | Start Docker Engine or Docker Desktop. On WSL verify integration for the current distribution. |
| CUDA 12.6 requirement rejected | Check the NVIDIA host driver and Docker GPU passthrough. The build ends at preflight. |
| Missing weights or AWS assets | Place the authorized model at the documented path. If bundled assets were removed, restore them with `bash hydra_mapping/scripts/prepare_external.sh aws`. |
| Stalled or failed compilation | Read the first failing package from plain progress. Rerun the same command after fixing the cause. Existing build caches are reused. |
| Display or OpenGL failure | Run from the local desktop with a valid `DISPLAY`. Check the Xauthority cookie on Linux and the OpenGL renderer preflight. The software renderer can be too slow for the sensor workload. |
| Unexpected engine or write-ownership error | Choose reuse or rebuild explicitly and check the writable state directory and host UID/GID. |
