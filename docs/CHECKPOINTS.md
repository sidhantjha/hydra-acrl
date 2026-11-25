# Checkpoints

## 2026-11-24 — Phase 1 and Phase 2

- Consolidated eleven pinned upstream trees locally, with Kimera-RPGO excluded from public staging. Migrated the Small House ROS package, planning scripts, saved baseline and experimental controller.
- Preserved the reference DSG SHA256 and reproduced the audited topology and route metrics through the new checkout. Added export validation tests using saved JSON.
- Made simulation resources and bridge package-local. Wired one EfficientViT semantic publisher and added managed shutdown and DSG export.
- Verified mapping preflight and static checks. The next checkpoint is a fresh Phase 3 planning installation and split mapping build, followed by a separately authorized Phase 4 runtime test.

## 2026-11-24 — Fresh planning environment verified

- The fresh `setup.sh --viz` installation imported `graph_io.py` from `.venv/lib/python3.12/site-packages/swarmx_planning/`. All eight installed package Python files matched the release source byte for byte. The test now accepts the exact release source file or the matching installed file in the release `.venv`. Probes rejected the original workspace, an unrelated environment and a mismatched installed file.
- Ran `.venv/bin/python -B -I -m unittest discover -s tests -v` without ROS. All four tests passed with the installed package. All four also passed using `PYTHONPATH="$PWD/src"` with the same interpreter and `-B -s`. `.venv/bin/python -B -I -m pip check` reported no broken requirements.
- Ran `.venv/bin/python -B -s scripts/find_small_house_route_switch.py`. It selected p13061 → p2473 and reproduced all four reference route metrics. The DSG SHA256 remains `fd98e8f2281006792a7f9ae60f42cdfac2b99c1ec47d4055d45db2ae4ecea392`.
- Ran `MPLBACKEND=Agg .venv/bin/python -B -s scripts/visualize_small_house_uncertainty.py --output-dir results/phase3-headless-D98lD5K9`. It produced a verified 2723×1974 PNG and the sweep CSV. The full split mapping build remains pending.

## 2026-11-24 — Small House launch argument forwarding

- The initial build compiled all 23 packages. Reproduced the original failure from `hydra_mapping/runs/20261124_170616_small_house` using the installed ROS Jazzy include action. The mapping-to-record include supplied no arguments, so the required argument check rejected `assets_models` even when the parent launch context already held its value.
- Forwarded `assets_models` and `gui` across both the mapping-to-record and record-to-world includes. The world uses them in `GZ_SIM_RESOURCE_PATH` and the GUI condition. The mapping launch forwards `force_rebuild` through the semantic wrapper to the installed `closed_set.launch.yaml`. Hydra consumes `run_directory` and `shutdown_grace` in the mapping launch. The spawn include still supplies `x`, `y`, and `z`. The semantic adapter has no launch arguments.
- Set both build stages in mapping `setup.sh` to `--executor sequential` with `MAKEFLAGS=-j1` and `CMAKE_BUILD_PARALLEL_LEVEL=1`. After sourcing Jazzy and the existing Hydra overlay, ran `MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1 colcon build --executor sequential --packages-select tb3_hydra_bringup` in `hydra_mapping/tb3_ws`. Exactly one package rebuilt. Setup preflight, Bash syntax and Python parsing passed, and all seven installed bringup launch files matched source byte for byte.
- Ran ROS Jazzy's launch service against the installed files with process dispatch intercepted. It resolved the AWS model path for Gazebo, enabled the GUI with `gui=true`, gave Hydra the supplied run directory and 17-second grace, and placed `force_rebuild: true` in the semantic node command. The delayed robot spawn, bridges, and semantic adapter also resolved.
- Ran `run_mapping.sh` headless with a fresh run directory and a private ONNX copy. The sandboxed run passed the launch argument check but hit DDS and Gazebo permission errors and a TensorRT CUDA initialization failure. The subsequent 25-second host run at `hydra_mapping/runs/launch-forwarding-host-20261124T230933-912180593Z` passed the argument check, started both bridges, and initialized Hydra's 720 × 480 camera from CameraInfo and TF. Gazebo reported unresolved portrait textures. TensorRT initialized CUDA and began building the engine. After the test sent SIGINT, the adapter reported that ROS shutdown had already been called, Gazebo exited with signal 11 after SIGTERM, and TensorRT required SIGKILL while building. See `console.log` in the host run directory.
- **Graph** — Hydra exited with status 0 and wrote its configuration and DSG JSON. The graph contained zero nodes and edges, and `export_dsg.sh` rejected it without writing an output.
- **Mesh** — The mesh-inclusive JSON contained mesh metadata without geometry.
- **Robot** — Gazebo confirmed Waffle entity creation. The waypoint controller was not executed.

## 2026-11-24 — Hydra-ACRL final release Part 1

- Added the four-pane native dashboard with readiness probes, an isolated Gazebo partition, stamped teleop with a focus key, an upstream streaming visualizer remap, run-scoped shutdown and automatic export.
- Rebuilt only `tb3_hydra_bringup`. The live image adapter exited cleanly, and resolving 19 pinned portrait mesh references removed missing texture warnings. The AWS dumbbell inertia remains upstream. Gazebo’s teardown segfault reproduced both in the dashboard and via its own stop service in an isolated simulator.
- **Graph.** The pre-release verified run `20261124_172404_small_house` retained 314 nodes, 948 edges and 138 PLACES nodes, with Hydra exit 0. The independent environment loaded that export. The release `--no-rviz` smoke run `hydra-acrl-20261124T235401Z-ecIl5Puy` exported 198 nodes, 593 edges and 94 PLACES nodes with Hydra exit 0.
- **Mesh.** The release smoke run saved a 3,918,623-byte mesh-inclusive JSON and a 2,492,004-byte PLY.
- **Robot.** The smoke test confirmed Gazebo GUI attachment, actual odometry changes from keystrokes injected into the teleop terminal, and one publisher on each of eight checked topics. All four panes exited cleanly. The waypoint controller was left outside the mapping launch.
- The default mode also opened both Gazebo and RViz windows and passed scripted control and shutdown checks. Hydra exported 218 nodes, 624 edges and 95 PLACES nodes with both mesh files. This run used window and process checks.
- The final headless test verified actual message stamps for odometry, semantics and DSG without a ROS CLI daemon. Hydra exported 223 nodes, 627 edges and 97 PLACES nodes with both mesh files.
- Both native overlays accepted colcon’s resume selection without rebuilding successful packages. Four planning regressions passed, and the historical route metrics and sweep CSV were reproduced. Five superseded scripts were archived locally, the empty stub was removed, and the working environments, results, reference and new DSGs were preserved.
- Applied Hydra-ACRL naming across the root documentation, modules and launcher. See the [implementation report](IMPLEMENTATION_REPORT.md#final-release-part-1--2026-11-24) for exact reproduction commands and publication exclusions.

## 2026-11-24 — Hydra-ACRL final release Part 2

- Implemented the CUDA-gated mapping image, standalone CPU planning image, Compose mounts, WSLg and native X11 paths, and an entry point that reuses the native dashboard.
- Docker identified the RTX 4080 in a small GPU container. The pinned CUDA 12.6.3 base rejected Windows driver 551.95. The mapping build exited at preflight with NVIDIA’s compatibility check intact. No mapping-container runtime result is claimed.
- Built the 475 MB Ubuntu 24.04 CPU planning image with Python 3.12 and Spark-DSG 1.1.3. All four container regressions passed, the 218-node native DSG loaded, and the sweep CSV reproduced byte for byte. A repeated build used cached layers, and a separate colcon probe preserved CMake objects across reinstall. The standalone WSLg probe reported hardware D3D12 OpenGL 4.6 and opened Gazebo and RViz windows through the tested forwarding path. Docker build progress is plain and the configured colcon invocations are sequential.
- Audited the actual Docker build context and kept local models, engine files, runtime data, native overlays, held derivatives and Kimera-RPGO out of the primary context. The file inventory and source and binary publication gates are in [PUBLICATION.md](PUBLICATION.md).
- The user personally verified the native dashboard. Original workspaces, Docker caches and existing workloads were preserved.
