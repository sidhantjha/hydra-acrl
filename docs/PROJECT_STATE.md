# Hydra-ACRL project state

Hydra-ACRL keeps live mapping and CPU-only saved-graph planning independently usable. The mapping overlay built all 23 packages before the release changes. The final native rebuild selected just the custom `tb3_hydra_bringup` package. Both overlay builds use colcon’s sequential executor and one native build job. The release setup can resume from colcon’s successful package records.

The four-pane dashboard is [launch.sh](../launch.sh). It waits for the Waffle and the command bridge, starts stamped interactive teleoperation after odometry, and connects the upstream Hydra visualizer to `/hydra/backend/dsg`. The dashboard sends a stop command, lets Hydra save, and validates exports after shutdown. The release guide covers GUI, headless and individual component startup. See the [root README](../README.md).

## Verified mapping and planning

- **Recorded graph.** In `hydra_mapping/runs/20261124_172404_small_house`, Hydra exited with code 0 and wrote a 600,529-byte DSG with 314 nodes, 948 edges and 138 PLACES nodes. Its SHA256 is `5c55fb44a6bf42baaabddac7551528480b04100520f1520a47995889c7bd95cd`. The independent Python environment loaded it.
- **Recorded mesh.** The same run wrote a 5,831,034-byte mesh-inclusive DSG and a 3,706,978-byte PLY.
- **Recorded robot operation.** Gazebo spawned the Waffle, and the run exercised RGB, depth, odometry, relays, TF, real TensorRT inference, manual teleoperation and live RViz.
- **Default dashboard.** The native run `hydra-acrl-20261124T235645Z-s60QjFtr` opened Gazebo and RViz windows, verified stamped keyboard motion and found one publisher on each of eight checked topics. Hydra exited with code 0, exported 218 nodes, 624 edges and 95 PLACES nodes, and saved the mesh-inclusive DSG and PLY. The independent planning environment loaded the export. GUI checks in this release used window and process probes.
- **Release launcher without RViz.** The native `--no-rviz` run `hydra-acrl-20261124T235401Z-ecIl5Puy` verified the four panes, Gazebo GUI attachment, stamped simulated motion via odometry, live semantics and DSG, and clean exit of all four panes. Hydra exited with code 0 and automatically exported 198 nodes, 593 edges and 94 PLACES nodes. Both mesh files were present. Gazebo’s server teardown still reported signal 11.
- **Final headless check.** Run `hydra-acrl-20261125T000802Z-AhbfA4of` verified received odometry, semantic and DSG message stamps without starting a ROS daemon. The keyboard PTY moved the robot, no duplicate nodes were seen, and Hydra exported 223 nodes, 627 edges and 97 PLACES nodes with both mesh files.
- **Planning.** All four reference regressions pass. The historical route metrics and sweep CSV were reproduced. The independent environment loads the historical reference and the newer export. The experimental waypoint controller uses hardcoded waypoints and does not consume a planned DSG route. Historical runs reported stalling.

## Runtime issues and publication

The image adapter now shuts down cleanly. Pinned AWS portrait JPEGs resolve from model-local texture directories. The remaining invalid inertia comes from the AWS dumbbell’s zero principal moment. The model physics remain as supplied. Gazebo’s native stop service also reproduced the teardown crash in an isolated simulator, so the verified save sequence remains in use.

The release keeps build outputs, runs, model weights, Kimera-RPGO, the working Python environment, and historical results outside Git publication. The verified bringup configuration and 64 pinned AWS models now ship with the checkout. Five superseded research scripts are archived locally. The intended destination is [sidhantjha/hydra-acrl](https://github.com/sidhantjha/hydra-acrl). The bringup and AWS notices cover the included derivatives. Project licensing, Kimera-RPGO redistribution and model/data distribution review remain open. See the [implementation report](IMPLEMENTATION_REPORT.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).

## Docker release preparation

The local Docker build has separate CPU planning and CUDA mapping targets, with the latter including both modules and the native dashboard. The CPU image `hydra-acrl:planning` was built on Ubuntu 24.04 and Python 3.12 with Spark-DSG 1.1.3. It uses 474,833,734 bytes of image space. All four regressions passed with a mounted reference, the sweep CSV reproduced byte for byte, and the container loaded the 218-node native export. Mapping tags are reserved for a successful CUDA-gated build.

The Docker engine saw the RTX 4080 in a small GPU probe. Both tested CUDA 12.6 base tags rejected Windows driver 551.95 under the NVIDIA container runtime. The pinned CUDA 12.6.3 mapping build stopped before compilation. The independent Jazzy WSLg probe used the D3D12 NVIDIA adapter at OpenGL 4.6 and opened Gazebo and RViz windows with a minimal world. This established graphics forwarding independently of the blocked CUDA 12.6 environment. Mapping packages, Gazebo, TensorRT, RViz, live graph generation and export remain pending inside the container. The user separately confirmed the unified native launcher.

The native setup and Docker build fetch the pinned Kimera-RPGO source automatically. An authorized EfficientViT ONNX remains the one manually supplied mapping input because MIT SPARK's published links returned 404. The Docker mapping target still needs a compatible host driver and its compiled dependency redistribution review remains open. [Publication inventory](PUBLICATION.md)

The isolated publication checkout built all 23 native packages from source and discovered the principal ROS packages in its fresh overlays. A separate isolated Gazebo run spawned the Waffle and received odometry, RGB and depth using the bundled world. The absent ONNX stopped the fresh dashboard before inference, graph generation and mesh export. The fresh Python 3.12 environment built Spark-DSG 1.1.3 and planned a route on a synthetic saved graph. The pinned CUDA preflight again rejected driver 551.95. [Fresh-clone test details](IMPLEMENTATION_REPORT.md#fresh-clone-simplification)
