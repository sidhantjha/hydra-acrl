# Hydra-ACRL mapping

The module uses a Hydra source overlay and a separate TurtleBot3 bringup overlay. `hydra.repos` records the eleven audited source revisions. Ten are vendored here. Kimera-RPGO is a pinned local dependency while the upstream license text is being resolved. See the [third-party notices](../THIRD_PARTY_NOTICES.md) for CMake downloads and source exclusions.

The package spawns the custom Hydra Waffle with 720×480 RGB and float depth in the AWS Small House world. The world retains the ceiling and Harmonic plugins. ROBOTIS supplies four meshes through the installed `turtlebot3_gazebo` share. Package-local bridge YAML covers clock, joints, odometry, TF, IMU, scan, calibration, depth and TwistStamped commands. RGB uses the existing `ros_gz_image` bridge.

The default run uses the semantic adapter, which forwards RGB, depth and calibration. The semantic launch owns one EfficientViT L2 ADE20K publisher at `/tesse/left_cam/semantic/image_raw`. The legacy fake-label adapter and interface are available for explicit diagnostics in a separate launch. The historical saved graph may have mixed fake and predicted labels. The release dashboard checks for real semantic messages and live backend graph updates.

Package-local Hydra configuration keeps the 25 m spatial window, 0.1–10 m sensor range, 0.1 m TSDF voxels, 0.3 m truncation, ADE20K labelspace and existing uHumans2 remaps. The TF chain is `world → odom → base_footprint → base_link → base_link_gt → left_cam`, with separate `world → map`. Camera translation is `[0.80, 0, 0.75]` and the audited optical rotation is retained. The Waffle SDF uses a small vertical joint offset where the historical static TF uses zero.

## Setup

The verified bringup and Small House assets ship with the checkout. Setup fetches Kimera-RPGO at its pinned revision. Provide the model before launching mapping. [Model provisioning](../README.md#install-native-mapping)

Use a clean Ubuntu 24.04 shell with ROS 2 Jazzy, Gazebo Harmonic, colcon, CMake, a C++ compiler, Python, and a compatible NVIDIA driver and development toolkit. The audited CUDA and TensorRT versions were 12.6 and 10.4. Configure `CUDAToolkit_ROOT`, `TensorRT_ROOT` or `ROS_JAZZY_SETUP` for nonstandard installations. Use rosdep and the vendored `install/*.yaml` manifests to review system dependencies (including GTSAM, Eigen, PCL, OpenCV, CLI11, nlohmann/json and ROS/Gazebo packages). The script checks principal tools, CUDA/TensorRT development files and the simulator packages. Colcon resolves compilation dependencies from the provisioned environment.

From the repository root:

```bash
bash hydra_mapping/setup.sh
```

Both overlays build sequentially. Use `--resume` to skip packages with successful build records after an interruption. The read-only `--check-only` option checks an already provisioned environment. The script uses system packages from the workstation and installs the project overlays into this checkout.

[`prepare_external.sh`](scripts/prepare_external.sh) fetches exact commits. Its `aws` mode can restore a removed Small House bundle from upstream. The repository includes only the 64 referenced models and textures. [Asset provenance](small_house/README.md)

## Run and export

Use the [root dashboard](../launch.sh) for the four-pane simulation. Follow the [manual startup sequence](#manual-startup) to run individual components. From this module in the configured mapping terminal:

```bash
mkdir -p runs
./scripts/run_mapping.sh --reuse-engine --run-dir runs/manual-01
# Press Ctrl+C once in the mapping terminal and wait for Hydra to save.
./scripts/export_dsg.sh runs/manual-01 runs/manual-01.json
```

[run_mapping.sh](scripts/run_mapping.sh) starts the server headless by default. Omit `--run-dir` to let it choose a unique run directory. Each run saves effective config, model hash and provenance. When the ONNX directory already contains an engine, the launcher prompts. Pass `--reuse-engine` for a compatible engine or `--rebuild-engine` to regenerate it in place. A missing engine is generated beside the ONNX file in a writable directory.

The dashboard exports automatically after shutdown. For a manual run, [export_dsg.sh](scripts/export_dsg.sh) takes the completed run directory and a new output JSON pathname. It checks Hydra’s exit, graph content and file integrity and writes the JSON plus an export report. The report records the mesh-inclusive JSON, PLY and Hydra configuration snapshot separately. The default Hydra SIGINT grace is 180 seconds.

In native release tests the image adapter exited cleanly. Gazebo still segfaulted on simulator teardown, including when its stop service accepted the request. Hydra saved independently. The AWS dumbbell's zero principal inertia remains as supplied. See the [verification report](../docs/IMPLEMENTATION_REPORT.md) for the recorded runs.

## Manual startup

Use the same environment in every terminal. Run from the checkout root. The example selects one ROS domain and one Gazebo partition for the manual run.

```bash
mapping="$PWD/hydra_mapping"
source "$mapping/scripts/mapping_environment.sh"
source_mapping_ros
configure_mapping_runtime
export ROS_DOMAIN_ID=42 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export GZ_PARTITION=hydra-acrl-manual
```

1. In the mapping terminal, start the headless server and mapping pipeline. Pick a new run name.

   ```bash
   mkdir -p "$mapping/runs"
   "$mapping/scripts/run_mapping.sh" --reuse-engine --run-dir "$mapping/runs/manual-01"
   ```

2. In another configured terminal, wait for `gz model --list` to show `hydra_waffle`. Start the server headless so it can finish loading the packaged world and spawning the robot before the GUI attaches. This ordering also lets the GUI resolve the same models as the server. Then attach only the GUI.

   ```bash
   gz model --list
   tb3=$(ros2 pkg prefix --share tb3_hydra_bringup)
   robotis=$(ros2 pkg prefix --share turtlebot3_gazebo)
   assets="$mapping/small_house"
   export GZ_SIM_RESOURCE_PATH="$tb3/models:$assets/models:$robotis/models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
   gz sim -g
   ```

3. In an interactive terminal, confirm the ROS velocity subscriber, Gazebo drive subscriber and actual odometry. Start one keyboard node.

   ```bash
   ros2 topic info /cmd_vel --verbose
   gz topic -i -t /cmd_vel
   ros2 topic echo /odom nav_msgs/msg/Odometry --no-daemon --once --timeout 10
   ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
   ```

4. In a configured terminal, start the live graph display.

   ```bash
   ros2 launch tb3_hydra_bringup small_house_visualizer.launch.py
   ```

## ROS data flow and TF

| Path | Role |
| --- | --- |
| Gazebo → `/camera/image_raw`, `/camera/depth/image_raw`, `/camera/camera_info` | RGB image bridge and configured ROS/Gazebo sensor bridges |
| `/tesse/left_cam/rgb/image_raw`, `/tesse/depth_cam/mono/image_raw`, `/tesse/left_cam/camera_info` | Adapter outputs with `left_cam` headers for Hydra and inference |
| `/tesse/left_cam/semantic/image_raw` | ADE20K labels from the single EfficientViT inference node |
| `/clock`, `/odom`, `/tf`, `/imu`, `/scan`, `/joint_states` | Simulator state and ROS bridges, with odometry and IMU relays to `/tesse` |
| ROS `/cmd_vel` → Gazebo `/cmd_vel` | Stamped ROS commands translated to Gazebo Twist |
| `/hydra/backend/dsg` → Hydra visualizer → RViz | Live scene graph updates |

The chain is `world → odom → base_footprint → base_link → base_link_gt → left_cam`. The separate `world → map` transform anchors graph visualization. See the local bridge configuration in [config/](tb3_ws/src/tb3_hydra_bringup/config/) and the [semantic interface launch](tb3_ws/src/tb3_hydra_bringup/launch/hydra_interface_semantic.launch.py).

## Stop, export and read a DSG

Press `k` in teleop, then run `./launch.sh stop SESSION` from another terminal or press **Ctrl+C** in **Mapping backend**. The dashboard stops teleop, sends zero velocity, closes the auxiliary processes and gives Hydra up to 180 seconds before ROS escalates its shutdown signal. Watch `mapping-backend.log` for the result. Detaching with **Ctrl+B**, then **D**, leaves mapping running.

A successful dashboard run writes `hydra_mapping/runs/SESSION/dsg.json` and `dsg.json.export.json`. Hydra’s raw output stays in `SESSION/mapping/hydra/`. Once shutdown and export finish, close the dashboard with `tmux -L SESSION kill-session -t SESSION`.

For a manual run, stop motion and close teleop, RViz and the Gazebo GUI with **Ctrl+C** in their terminals. Press **Ctrl+C** once in the mapping terminal, wait for shutdown, then export to an unused path.

```bash
./hydra_mapping/scripts/export_dsg.sh hydra_mapping/runs/manual-01 hydra_mapping/runs/manual-01.json
cd hydra_task_and_motion_planning
.venv/bin/python scripts/inspect_small_house.py --dsg ../hydra_mapping/runs/manual-01.json
```

The exporter checks Hydra’s exit record and graph contents. It records the mesh-inclusive JSON and PLY independently. To use a DSG from Python, pass its path to [`load_dsg`](../hydra_task_and_motion_planning/src/swarmx_planning/graph_io.py), then pass the graph to [`extract_places`](../hydra_task_and_motion_planning/src/swarmx_planning/places.py).

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Launch asks for an engine choice or reports a TensorRT mismatch | Select a compatible engine explicitly or regenerate it in a writable model directory. Check the CUDA driver and `TensorRT_ROOT`. |
| Robot, velocity bridge or odometry readiness times out | Read `readiness.log` and `mapping-backend.log`. Confirm the overlays, ROS domain, Gazebo partition and pinned Small House assets. |
| Gazebo GUI has missing models | Attach after spawn with the custom, AWS and ROBOTIS model paths from the manual steps. Rerun `prepare_external.sh aws` to refresh portrait texture references in an older cache. |
| Keyboard input has no effect | Press F3, verify `/cmd_vel` is `geometry_msgs/msg/TwistStamped` and verify a bridge subscriber. |
| RViz is empty | Use fixed frame `map` and check for messages and a visualizer subscription on `/hydra/backend/dsg`. TensorRT generation can delay the first update. |
| Export reports an empty or invalid graph | Inspect Hydra’s exit record and backend files. Move through the house and allow inference and graph updates before stopping a new run. |
| Reference tests are skipped | Place an authorized reference DSG at `hydra_task_and_motion_planning/experiments/small_house/run_01/dsg.json`. Check the hash in the planning guide. |
