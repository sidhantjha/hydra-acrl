# Hydra-ACRL implementation and verification report

2026-11-24

The Phase 1 and Phase 2 sections record the migration and its validation at that time. [Final release Part 1](#final-release-part-1--2026-11-24) records the later native runs, cleanup and reproduction commands.

## Executive summary

**COPIED AND VERIFIED** — Consolidated the audited implementation in two modules. Verified the source copies and reproduced the reference DSG byte for byte. Ten upstream repositories are vendored as ordinary files. The exact eleventh tree, Kimera-RPGO, is installed locally and Git-ignored pending license review.

**IMPLEMENTED AND STATICALLY VALIDATED** — Added split-overlay setup, package-share simulation resources, the local bridge, a single inference path, managed shutdown and DSG export, and independent planning packaging. **RUNTIME VERIFIED** applies to the saved-graph tests, direct route search, headless static plot, export fixture, local asset preparation and setup preflight. **IMPLEMENTED BUT NOT RUNTIME TESTED** applies to ROS simulation, inference, Hydra mapping and live shutdown.

## Actual structure

```text
README.md, AGENTS.md, .gitignore, THIRD_PARTY_NOTICES.md
hydra_mapping/
  README.md, setup.sh, hydra.repos
  patches/                          audited Hydra changes and AWS inertia patch
  scripts/                          preparation, preflight helpers, run and export
  hydra_ws/colcon_defaults.yaml
  hydra_ws/src/                     ten vendored trees and ignored local kimera_rpgo
  tb3_ws/src/tb3_hydra_bringup/      launch, config, custom model, world, notices, adapters
  external/small_house/             ignored pinned simulation assets
hydra_task_and_motion_planning/
  README.md, pyproject.toml, requirements.txt, setup.sh
  src/swarmx_planning/              copied Python API and experimental control/
  scripts/, experiments/, tests/
docs/
  ARCHITECTURE.md, PROJECT_STATE.md, CHECKPOINTS.md, IMPLEMENTATION_REPORT.md
```

`runs/` and planning `results/` are created on use. The fresh checkout was verified as `/home/swarmx/swarmx-3dsg-release`, origin `https://github.com/sidhantjha/swarmx-3dsg-planning.git`, HEAD `83ea9ef`. Its history contains the initial scaffold and no tracked virtual-environment history. The redundant root package marker was moved into the planning module.

## Phase 1 source-copy gate

**COPIED AND VERIFIED** — Selected tracked working-tree files from the eleven dependencies and a specific manifest of Small House integration resources. Verified local HEADs against all eleven audit SHAs and recorded their URLs in `hydra.repos`. SHA256 reads matched on all 1,668 initial copies (15,775,158 bytes). Final verification rehashed the corresponding originals, including the system bridge. All matched the initial copy inventory. No original repository, audit, graph or model was edited.

| Copied inventory | Files | Initial bytes |
| --- | ---: | ---: |
| Hydra | 475 | 3,760,843 |
| Hydra-ROS | 190 | 815,064 |
| Spark-DSG | 167 | 1,826,809 |
| semantic_inference | 130 | 2,019,628 |
| config_utilities | 163 | 955,854 |
| Spatial-Hash | 38 | 154,602 |
| Ianvs | 42 | 106,584 |
| Kimera-PGMO | 158 | 2,208,552 |
| Kimera-RPGO (local only) | 81 | 269,329 |
| pose_graph_tools | 41 | 45,160 |
| TEASER++ | 138 | 1,987,083 |
| Small House bringup, bridge and colcon defaults | 18 | 68,155 |
| Planning API, scripts and experiment files | 24 | 1,553,165 |
| Historical controller and launch reference | 2 | 3,399 |
| Original AWS notice | 1 | 931 |

The eleven selected source trees totaled 14,149,508 bytes before Phase 2. The final dependency workspace is 14,149,947 apparent bytes including the local Kimera-RPGO marker. The checkout uses 96 MiB on disk excluding Git metadata and workspace tool directories. The dependency workspace accounts for 19 MiB of that total. The initial code copy contained no symlinks or nested Git metadata. Generated workspace output was excluded. Upstream source directories named `install` contain installation manifests, and Kimera-PGMO's source `log` directory contains an ignore marker. Both were retained.

The inventory excluded Hydra's large overview GIF, optional TEASER++ examples and TEASER++ test clouds, and the optional semantic zoo Mask2Former gitlink. TEASER++ tests are disabled for the mapping build. The Small House model and world are byte-identical copies. The separate local AWS preparation exported 64 world-referenced model directories and the original notice, totaling 351 files including the revision marker and about 76.2 MB on an apparent-byte basis. All SDF model URIs used by the world and robot resolved against the AWS export and installed ROBOTIS meshes. The corrected ShoeRack SDF matched the audited local source after patching. The first patch attempt was silently skipped by Git's parent checkout discovery. The preparation script now isolates Git discovery for the patch and checks the applied state in reverse.

The workflow excludes legacy TB4 code under `hydra_tb4_autonomy/{hydra_tb4_stack,tb4_ws,hydra_ws/src/hydra_user_launch}`, the backup at `hydra_project/tb3_ws_claude_backup`, and the warehouse/lakehouse, offline and mixed controller launch files under the original TB3 package. The unchanged controller and original launch reference were preserved in planning. The 108,965,154-byte combined GIF and other historical GIFs remain in the original planning workspace.

The 556,994-byte DSG SHA256 is `fd98e8f2281006792a7f9ae60f42cdfac2b99c1ec47d4055d45db2ae4ecea392`. The associated PNG, CSV and metadata were preserved, alongside the historical uHumans2 result notes. The Small House data and generated figure are ignored for public staging.

## Phase 2 implementation

**IMPLEMENTED AND STATICALLY VALIDATED**

- Mapping resource lookup uses ROS package shares. The bringup package installs its launch, configuration, custom Waffle model, world and notices. The two Gazebo processes are the simulation server and optional GUI. The attached ROS launch owns the mapping processes.
- The bridge is a byte-identical package-local copy of the audited modified ROS installation file. Static checks covered ROS/Gazebo types and directions, including depth and TwistStamped. RGB remains on the separate image bridge. The default workflow depends on no edited system Waffle or bridge files.
- Package-local `hydra.yaml` and `hydra_input.yaml` retain the audited 25 m mapping radius, 0.1–10 m sensing, 0.1 m voxels and 0.3 m truncation. A project-owned launch uses the same Hydra input/core/labelspace/sink/LCD layers as the historical stack, with ADE20K, simulated time, explicit historical frame names/remaps, disabled loop closure/visualizer and a per-run save path. The audited upstream YAML edits are preserved in reference patches. Generic TB4 frame defaults and the empty OAK-D configuration were restored to upstream content.
- The Small House simulation selects the semantic adapter. One copy of the existing semantic wrapper owns the EfficientViT inference node. The five historical static TF edges used by the run are retained, with Gazebo owning odom → base_footprint. Fake labels are available only through the separate legacy interface.
- `setup.sh` verifies OS/ROS, principal tools and packages, CUDA/TensorRT files, pinned local assets and model hash, then builds the included Hydra overlay followed by the TurtleBot3 overlay. The dependency preparation script can export from pinned upstream Git revisions or a supplied local checkout. The online retrieval path was inspected but not run.
- The launcher records model and asset provenance and copies the effective configuration inputs. Hydra has a configurable 180-second SIGINT grace period by default. Export waits under a file lock, requires a clean recorded Hydra process exit and validates graph structure, PLACES nodes and edge endpoints. It writes SHA256 and separate mesh/configuration presence and size in a sidecar. The test covers valid, empty, malformed, terminated and duplicate-output cases.
- Planning supports an isolated Python 3.12 environment using the vendored Spark-DSG 1.1.3 binding or a supplied compatible wheel. Visualization dependencies are optional. CLI input and output paths are checkout-relative by default and replace the audited home-directory runtime paths. XY/XYZ costs, A*, NetworkX, thresholds, filters and endpoint exemptions retain the copied algorithms.

## Files changed from the copied baseline

26 copied files changed. Eight were vendored files (five YAML restorations and three CMake pinning edits). Six were bringup files (`package.xml`, `setup.py`, `small_house_world`, `small_house_record_run`, `spawn_robot` and `hydra_interface_semantic` launch files). Twelve were planning entry points (both sweep scripts, both clearance/A* plots, both route animations, the final demo, both ground checks, Small House inspection, route-switch search and uncertainty visualization). The empty `inspect_places.py` stub, reusable planning API, adapter code, model/world, graph, result files and controller were preserved. The AWS notice moved into the bringup notice directory byte for byte. New setup, orchestration, packaging, helper, test and documentation files are separate from the 26 copied-file edits.

See [third-party notices](../THIRD_PARTY_NOTICES.md) for exact revisions, existing local edits and build downloads.

## Validation and numerical results

| Check | Evidence |
| --- | --- |
| Syntax and manifests | **IMPLEMENTED AND STATICALLY VALIDATED** — 168 Python, 13 Bash, 136 YAML, 27 XML/SDF and 9 TOML files passed. The XML checks included 23 ROS manifests. One intentionally invalid upstream YAML fixture was confirmed invalid. The TEASER++ Conda recipe was rendered with test values before validation. |
| Resources and ROS launch | **IMPLEMENTED AND STATICALLY VALIDATED** — Constructed seven bringup launch descriptions, assembled the mapping actions with mocked package shares and inspected setup.py resource destinations. No launch actions were executed. Colcon discovered all 23 packages. The 15 ament packages resolved through the ROS index, and the eight CMake-only packages had their installed colcon manifests. Checked 64 AWS models, four robot meshes, ceiling, dual 720×480 cameras, bridge, historical settings and semantic wiring. |
| Setup preflight | **RUNTIME VERIFIED** — `setup.sh --check-only` passed on Ubuntu 24.04 with Jazzy, CUDA 12.6 and TensorRT 10.4 using the audited model cache read-only. A configure-only dependency probe also resolved CUDA and TensorRT. No full colcon build ran. |
| Saved-graph regressions | **RUNTIME VERIFIED** — Four passed, zero failed, with the original Python 3.12 interpreter in a cleared child environment, from this checkout and without ROS. Direct default script and headless visualization with explicit DSG path also exited successfully. |
| Git and size | **COPIED AND VERIFIED** — No staged changes, gitlinks, nested Git metadata, external source symlinks, copied environment, or compiled workspace output. Dependency manifests and test fixtures remained visible to Git, with the intentional local exclusions described above. |

The release fixture loaded **246 PLACES nodes**, **971 PLACES edges** and unfiltered component sizes **242 and 4**. The **0.8 m** vertical filter retained **555 edges**, with **213** nodes in the start component. The migrated heuristic selected **p13061 → p2473**, with goal **z = 1.5 m**. The same existing A* implementation was called for the fixed endpoints, using a tolerance of 1e-6 m.

| Clearance threshold (m) | XY route length (m) | Interior clearance (m) | Nodes |
| ---: | ---: | ---: | ---: |
| 0.40 | 11.492680218053675 | 0.44721361994743347 | 6 |
| 0.50 | 11.848104306169116 | 0.63245546817779541 | 7 |
| 0.70 | 12.098943976678365 | 0.91651517152786255 | 8 |
| 1.00 | 12.428330777244669 | 1.0 | 6 |
| 1.10 | No feasible route | | |
| 1.20 | No feasible route | | |

Exact regression command used from the planning module, with all temporary writes routed into the release workspace:

```bash
release=$(cd .. && pwd)
scratch="$release/hydra_mapping/external/validation"
mkdir -p "$scratch"
env -i HOME="$scratch" PATH=/usr/bin:/bin LANG=C.UTF-8 PYTHONPATH="$PWD/src" \
  PYTHONDONTWRITEBYTECODE=1 SWARMX_TEST_TMP="$scratch" \
  /home/swarmx/swarmx-3dsg-planning/.venv/bin/python -B -s -m unittest discover -s tests -v
```

## Controller, limitations and blockers

**HISTORICAL EVIDENCE** — The controller uses hardcoded waypoints and stalled in historical simulation. The reference graph may reflect both predicted and fake labels. Historical logs show Hydra received SIGTERM during mesh serialization after a five-second allowance. The historical mesh-inclusive JSON and configuration snapshot are empty.

**NOT IMPLEMENTED** — Automatic control from DSG paths, calibrated uncertainty, continuous collision checking, traversability certification and task-level planning. The XY experiment and vertical filter are graph operations. The controller was not executed or tuned.

**BLOCKED** — Public release depends on Kimera-RPGO license text, project-owned licensing, derivative model/bridge and asset attribution review, and authorization for model weights and the research graph/figures. Remote freshness and availability of the exact historical ONNX via upstream documentation were not verified. A clean build needs provisioned system libraries, an authorized local model, and a supported GPU environment. The data and RPGO exclusions prevent accidental ordinary staging but cannot substitute for publication review.

**IMPLEMENTED BUT NOT RUNTIME TESTED** — Fresh package installation, split-overlay compilation, DDS publisher count, real sensor encodings and TF linkage, TensorRT generation, Gazebo/GUI operation and actual shutdown export. These were outside Phase 2 authorization. The saved-file test verifies only the export consumer and synthetic lifecycle status. Historical GVD failures, output completeness and simulation coverage require runtime investigation if reproduced.

## Phase 3 and Phase 4 commands

Phase 3 from the repository root in clean shells. Provision the platform prerequisites and authorized artifacts first.

```bash
cd hydra_task_and_motion_planning
./setup.sh --viz
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/find_small_house_route_switch.py --dsg experiments/small_house/run_01/dsg.json
cd ../hydra_mapping
./scripts/prepare_external.sh rpgo
./scripts/prepare_external.sh aws
export SEMANTIC_INFERENCE_MODEL_DIR=/absolute/path/to/provisioned/models
./setup.sh --check-only
./setup.sh
```

Phase 4 after the build and runtime authorization. Use an unused run name and a writable model directory. Omit `--rebuild-engine` when the directory has only ONNX.

```bash
cd hydra_mapping
export SEMANTIC_INFERENCE_MODEL_DIR=/absolute/path/to/provisioned/models
mkdir -p runs
./scripts/run_mapping.sh --gui --run-dir runs/phase4-smoke --shutdown-grace 180 --rebuild-engine
```

From another terminal in `hydra_mapping`, observe the mapping while it is running. Use the same ROS domain as the mapping process.

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic info /tesse/left_cam/semantic/image_raw --verbose
ros2 topic info /tesse/depth_cam/mono/image_raw --verbose
ros2 run tf2_ros tf2_echo world left_cam
```

After manual coverage, send Ctrl+C once in the mapping terminal. Wait for the managed run to exit, then verify graph, mesh and configuration separately.

```bash
./scripts/export_dsg.sh runs/phase4-smoke runs/phase4-smoke.json
cd ../hydra_task_and_motion_planning
.venv/bin/python scripts/inspect_small_house.py --dsg ../hydra_mapping/runs/phase4-smoke.json
```

## Checklist

- [x] Verify checkout, pinned source, notices and reference graph.
- [x] Consolidate source and apply targeted portability changes.
- [x] Pass syntax, resource, hygiene and saved-graph regression checks.
- [x] Keep release-only work local, with no staging, commits or pushes.
- [ ] Resolve publication blockers.
- [ ] Validate fresh installation and full build in Phase 3.
- [ ] Observe one real semantic publisher, TF continuity and shutdown export in Phase 4.

## Final release Part 1 — 2026-11-24

### Launcher and native builds

- The root dashboard reuses `run_mapping.sh` and `export_dsg.sh`, uses a separate tmux server and Gazebo transport partition for each run, and reserves its ROS domain during mapping and export. The four titled panes remain available after process exit. The mapping pane logs bounded probes for the robot, stamped bridge, actual odometry, the teleop publisher, the visualizer subscription, semantic images and live DSG updates.
- The visualizer wrapper includes the upstream streaming launch and applies the topic remap. Hydra, mapping parameters, the Waffle SDF, the bridge schema, and XY, XYZ and NetworkX planning implementations are unchanged.
- The image adapters now handle interrupted ROS contexts and use `rclpy.try_shutdown()`. Only `tb3_hydra_bringup` was rebuilt. Installed launch and package files were checked through native startup. Colcon discovered all 23 packages. The 15 ament packages resolved through the ROS index, and the eight CMake-only packages had their installed colcon manifests. `setup.sh --resume` selected zero previously successful packages in both populated overlays.
- Colcon displays the discovered topological order and emits each package’s actual start, finish or failure in sequential execution. An injected required-dependency failure confirmed that setup stopped before invoking the downstream overlay. Resume uses colcon’s build records and is intended for an interrupted build using the same sources and options.

### Runtime findings and evidence

| Area | Evidence |
| --- | --- |
| Recorded mapping run | `hydra_mapping/runs/20261124_172404_small_house`. Hydra exit 0. 314 nodes, 948 edges, 138 PLACES nodes, 600,529 bytes. SHA256 `5c55fb44a6bf42baaabddac7551528480b04100520f1520a47995889c7bd95cd`. The independent planning environment confirmed 514 PLACES edges and two connected components of 107 and 31 nodes. |
| Recorded mesh | 5,831,034-byte mesh-inclusive DSG and 3,706,978-byte PLY in the recorded run. |
| Recorded robot and visualization | The verified run exercised robot spawn, RGB, depth, odometry, relays, TF, real TensorRT inference, manual stamped teleop, and live visualization in RViz. |
| Native headless dashboard | `hydra-acrl-20261124T234358Z-fv2n8Jxn`. All readiness stages passed, including one remapped visualizer subscription and observed live backend updates. The stop command exported 118 nodes, 340 edges and 69 PLACES nodes. Hydra exit 0. Mesh-inclusive JSON 1,742,531 bytes, PLY 1,064,962 bytes. |
| Final headless verification | `hydra-acrl-20261125T000802Z-AhbfA4of`. The updated probes confirmed received stamps for odometry, semantic images and backend DSG without a ROS CLI daemon. Keyboard motion and one publisher on each of eight topics were verified. Hydra exited 0 and exported 223 nodes, 627 edges and 97 PLACES nodes (417,886 bytes, SHA256 `a1da041d46c28633c4d887db00202cf05cbe96bdeab13189c3b5b21100a1033b`). Mesh-inclusive JSON 3,937,683 bytes, PLY 2,480,179 bytes. |
| Native default dashboard | `hydra-acrl-20261124T235645Z-s60QjFtr`. The Gazebo and RViz windows were detected, all startup stages reached live mapping, and scripted keyboard input changed odometry to (0.111, 0.034) m. The ROS graph probe observed no duplicate nodes and one publisher on each of eight checked topics. All four panes exited with code 0. Hydra exported 218 nodes, 624 edges and 95 PLACES nodes (415,367 bytes, SHA256 `6022e9ce535d4aa989e42167bf78d5f90dd4004d46d2d0034e5f46fefae9a131`). The mesh-inclusive JSON was 3,844,446 bytes and the PLY was 2,415,287 bytes. The independent planning environment loaded the export. |
| Native GUI without RViz | `hydra-acrl-20261124T235401Z-ecIl5Puy`. Four titled panes had PTYs. Gazebo attached after spawn, and a window probe reported `Gazebo Sim`. Programmatic keystrokes in the teleop PTY moved odometry from approximately (0, 0) to (0.132, 0.041) m. No duplicate nodes were observed. A ROS graph probe found one publisher each for stamped velocity, odometry, camera RGB, relayed RGB, relayed depth, camera info, ADE20K semantics and backend DSG. The visualizer subscription was recorded separately by launcher readiness. |
| GUI-run graph and mesh | The stop command sent zero velocity, all four panes exited with code 0, and Hydra exported 198 nodes, 593 edges and 94 PLACES nodes. The JSON is 384,266 bytes, SHA256 `643c6f4d520f949848f9940468ea180da051f2b3cbf2f702787ce2e36c1d60a7`. Mesh-inclusive JSON 3,918,623 bytes, PLY 2,492,004 bytes. |
| Gazebo teardown | Server exited with signal 11 in the managed dashboard. In a separate Gazebo-only probe with the same world and robot, `/server_control` accepted `stop: true` and Gazebo still exited 139. This isolated the fault from Hydra and the ROS launcher. A physics or rendering change would require separate investigation. Hydra exit and export remained independent. |
| Texture and inertia warnings | Nineteen AWS DAE meshes used dangling paths. Asset preparation now copies the exact JPEGs at the pinned revision and points the meshes at their local material texture directories. A fresh 64-model asset export verified 19 paths against 18 byte-identical upstream JPEGs. The native logs no longer reported missing portraits. The remaining invalid inertia is the AWS dumbbell link’s `iyy = 0`. Its physics were preserved. The prior ShoeRack typo fix remains applied. |
| Failure handling | Tested unknown and mutually exclusive options, missing explicit engine choice, invalid ROS domain, no-display GUI request, and invalid stop target. An occupied ROS domain was rejected with the pane retained. An early native readiness timeout stopped the owned processes and saved diagnostics. The final timeout and discovery checks were adjusted from those traces. |
| Engine rebuild option | Checked launcher argument forwarding and rebuild preflight with a tmux stub. Native tests reused the existing engine. |
| Planning | Installed-environment four-test suite and `pip check` passed. The historical XY experiment reproduced all four reference route metrics and infeasibility thresholds. The generated sweep CSV was byte-identical to the saved reference. The XYZ sweep and route figure also ran. Both NetworkX animation commands produced GIFs, and the 2D command also produced an MP4. The uHumans2 notes remain historical evidence. The accessible archived graphs were smaller and lacked the recorded endpoint pair, so those historical numbers could not be reproduced with the available files. |

The GUI smoke tests observe process startup, X window presence and simulated odometry. The earlier 314-node run supplies the separate evidence for manual GUI inspection and driving.

### Cleanup audit

| Classification | Paths and disposition |
| --- | --- |
| Essential source | Kept all `src/swarmx_planning/` Python modules, the experimental `control/` sources and reference launch, both native workspace source trees, and the custom Gazebo and ROS files. Preserved upstream layouts, source notices and build dependencies. |
| Required configuration | Kept both `setup.sh` files, Python package metadata and used requirements, colcon defaults, `hydra.repos`, migration patches, package manifests, bridge and Hydra configs, the robot SDF and world. |
| Runnable examples | Kept the mapping runner, asset preparation and exporter. Kept seven planning commands for DSG inspection, XY reproduction, XYZ sweep and plot, uncertainty figures, and 2D/3D NetworkX animation. The shared planning argument helper now requires an explicit input DSG. The maintained XYZ sweep covers the alternate sweep’s route-search purpose. |
| Regression tests | Kept the four existing tests in `tests/test_reference.py`. The fixture is passed explicitly to the route-switch script. |
| Historical artifacts | Kept `experiments/small_house/run_01_metadata.md`, `experiments/uhumans2/baseline_results.md`, the reference graph, its original PNG and CSV, all previous mapping runs and the newly generated DSG. Existing outputs remain ignored locally. |
| Generated and temporary | Retained the working `.venv/`, Python and ROS build trees and installed overlays. Git excludes `.venv/`, `build/`, `install/`, `log/`, `dist/`, `results/`, `runs/`, `external/`, caches, egg metadata, local Kimera-RPGO, model weights, raw bags and local reference data. VS Code hides generated paths without hiding vendored `install/*.yaml` manifests or source. |
| Superseded and obsolete | Moved `analyze_uncertainty_sweep.py`, `check_ground_edges.py`, `check_ground_slice.py`, `compare_clearance_routes.py` and `make_small_house_final_demo.py` to ignored `hydra_task_and_motion_planning/experiments/archive/`. Removed the empty `inspect_places.py` stub. Retained the older fake-label diagnostic because its standalone launch still calls the corresponding adapter. |

The audit traced imports, package data, launch includes, setup scripts, docs and shell references before changing the maintained script list. The existing upstream container assets remain with their sources. Future Hydra-ACRL containers will need the two current overlay roots and separately provisioned local dependencies. No project Docker files were added. See the [repository tour](../README.md#repository-tour) for the visible release tree.

### Reproduction commands

From the checkout root, with the prepared overlays, authorized ONNX, compatible engine and desktop available:

```bash
./launch.sh --help
ROS_DOMAIN_ID=74 ./launch.sh --reuse-engine
# Press F3, use i and j to move, then k to stop motion.
# In a second terminal use the session name printed by launch.sh.
./launch.sh stop SESSION
tail -f hydra_mapping/runs/SESSION/mapping-backend.log
```

Use `--headless` to omit Gazebo GUI and RViz, or `--no-rviz` to exercise Gazebo GUI and keep the streaming visualizer without RViz. Run `tmux -L SESSION list-panes -F '#{pane_title} #{pane_tty} #{pane_dead_status}'` to inspect the dashboard. For an existing cache, `./hydra_mapping/scripts/prepare_external.sh aws /path/to/authorized/local/aws-checkout` refreshes the pinned portrait assets.

```bash
./hydra_mapping/setup.sh --check-only
./hydra_mapping/setup.sh --resume
(
  cd hydra_mapping/tb3_ws
  source /opt/ros/jazzy/setup.bash
  source ../hydra_ws/install/local_setup.bash
  MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1 colcon build --base-paths src \
    --executor sequential --packages-select tb3_hydra_bringup
)
```

```bash
cd hydra_task_and_motion_planning
.venv/bin/python -B -I -m unittest discover -s tests -v
.venv/bin/python -B scripts/find_small_house_route_switch.py --dsg experiments/small_house/run_01/dsg.json
.venv/bin/python -B scripts/inspect_small_house.py --dsg ../hydra_mapping/runs/20261124_172404_small_house.json
mkdir -p "$PWD/results"
out=$(mktemp -d "$PWD/results/reproduce-XXXXXXXX")
MPLBACKEND=Agg .venv/bin/python -B scripts/visualize_small_house_uncertainty.py \
  --dsg experiments/small_house/run_01/dsg.json --output-dir "$out"
cmp "$out/uncertainty_sweep.csv" experiments/small_house/run_01/uncertainty_sweep.csv
```

The work is local. Review publication permissions in [third-party notices](../THIRD_PARTY_NOTICES.md) before staging. The new destination and reserved container names are in [architecture](ARCHITECTURE.md).

## Final release Part 2 — 2026-11-24

### Container design and build gate

[Dockerfile](../Dockerfile) provides a thin Ubuntu 24.04 CPU runtime and a local CUDA mapping runtime including the same Python environment. The image copies installed overlays at their original in-image paths and calls the native dashboard through [entrypoint.sh](../docker/entrypoint.sh). The entry point keeps the container alive when the tmux client detaches and forwards container shutdown to the run-scoped stop command.

| Stage | Evidence or configuration |
| --- | --- |
| Host preflight | Docker 29.8.0, Compose 5.5.1, Docker Desktop 4.92.0 and BuildKit 0.33.0. 32 CPUs, 15.4 GiB daemon memory, approximately 10–11 GiB available WSL RAM and 4 GiB swap. About 931 GiB available inside Docker’s filesystem and 143–145 GiB on Windows C:. Initial Docker image usage was 17.38 GB and build cache was 4.222 GB. No existing caches or workloads were removed. |
| NVIDIA GPU and exact base | The cached Jazzy ROS base ran `nvidia-smi -L` with `--gpus all` and identified the 12 GB RTX 4080 Laptop GPU. The NVIDIA runtime then rejected CUDA 12.6.0 and the pinned CUDA 12.6.3 base image on driver 551.95 with `unsatisfied condition: cuda>=12.6`. The selected devel manifest declares the same minimum. The full build script exited at that gate. CUDA 12.6 minor compatibility on the native host does not satisfy the container’s requirement. [CUDA 12.6.3 release notes](https://docs.nvidia.com/cuda/archive/12.6.3/cuda-toolkit-release-notes/index.html) |
| Exact packages | Docker Hub advertised Ubuntu 24.04, the CUDA 12.6.3 base and devel amd64 manifests, and the Dockerfile pins their platform digests. The manifest declared CUDA 12.6.3. Ubuntu 24.04’s NVIDIA package index provides all eight TensorRT 10.4.0.26 CUDA 12.6 headers and libraries. APT simulation in the pinned CUDA base resolved all eight exact versions. Pinning the development packages alone caused APT to select newer dependencies, so the Dockerfile pins the full matching set. The ROS Noble apt-source installer was hash-checked, and Noble/ROS apt resolution in a clean Jazzy container found the configured dependencies, including ROS GTSAM 4.2.0 and Gazebo Harmonic through the Jazzy vendor packages. [NVIDIA package archive](https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/), [ROS apt-source release](https://github.com/ros-infrastructure/ros-apt-source/releases/tag/1.3.0) |
| Package progress and cache design | APT stages cover native libraries, exact TensorRT and ROS/GUI dependencies. The Hydra workspace is a 22-package sequential colcon invocation, followed by the single bringup package, all with `MAKEFLAGS=-j1` and `CMAKE_BUILD_PARALLEL_LEVEL=1`. The first colcon layer depends on the finished planning wheel, so both compiler jobs cannot overlap. The progress formatter numbers colcon start and finish events from 01 through 23. A probe replayed events in the actual discovered order and verified the full numbering and immediate failure propagation with a stubbed required-package error. `pipefail` preserves the build failure, and Docker stops before the next layer. The BuildKit cache mounts retain CMake build trees. Overlay install paths live in normal image layers. If a compile layer is interrupted, the next build reuses the cache and lets colcon recreate the overlay without using stale success flags to skip installation. A real sequential colcon probe rebuilt a fresh install layer for `pose_graph_tools` and reused the original CMake objects. The installed library and recorded object timestamps matched byte for byte. The CPU stage also reused its dependency, wheel and runtime layers on a second build. |
| Context and local assets | A scratch `COPY .` export was used to audit the actual Docker context. The corrected exclusions reduced its logical contents from about 203 MB transferred on the first scan to 7,226,543 bytes across 1,545 regular files in the corrected primary context. No workstation installs, native build trees, graphs, models, engines, Kimera-RPGO or held bringup files were present in the corrected primary context. A separate local-only context provisions pinned Kimera-RPGO and the three checksum-verified derivatives. Model and AWS assets enter at runtime through read-only mounts. Engine cache, run output and results are writable by the host UID/GID. |
| Image sizes | The CPU image built locally. Docker reports 474,833,734 bytes of image size and about 110 MB of content. The full mapping build was blocked before creating either tag, `hydra-acrl:latest` or `hydra-acrl:1.0.0`. Its size is unmeasured. |

### Docker and native verification boundary

- **Planning container.** The CPU target builds and imports Spark-DSG 1.1.3 and the planning package on Python 3.12. All four regressions passed against the read-only reference mount. The CPU container loaded the 218-node, 624-edge native export with 95 PLACES nodes. Its historical sweep CSV matched byte for byte, and the generated PNG and CSV were owned by host UID/GID 1000:1000. `pip check` passed.
- **Static and CLI checks.** BuildKit checked the mapping target with no build warnings. Compose configuration, Bash syntax and option handling passed. The CLI reported missing ONNX, missing AWS assets, missing display, missing local mapping image and conflicting or absent engine choices. The opt-in EGL flag resolved only when requested in the source launch check. A tmux PTY test with a stand-in backend verified attachment, survival after detach and a stop request on SIGTERM.
- **Rendering.** A separate Jazzy container used GPU passthrough and forwarded the WSLg X socket, read-only WSL libraries, `/dev/dxg`, and the Mesa D3D12 adapter selection. `glxinfo -B` returned OpenGL 4.6 and the D3D12 RTX 4080 renderer. The initial unselected probe used llvmpipe. The Compose WSLg service uses the verified adapter settings. A second standalone Jazzy probe installed the official Gazebo and RViz packages, started a minimal Gazebo server, waited for its scene service, then attached the Gazebo GUI and started RViz. An X window probe detected both, and RViz reported OpenGL 4.6. This probe used the same WSLg socket, device and environment settings. The native Linux Xauthority path and the Gazebo EGL path remain unverified. [Microsoft WSLg container examples](https://github.com/microsoft/wslg/blob/main/samples/container/Containers.md), [Gazebo Harmonic headless rendering](https://gazebosim.org/api/sim/8/headless_rendering.html)
- **Graph, mesh and robot in the mapping container.** CUDA 12.6 blocked this environment before compilation. All 23 package discovery, robot spawn, bridges, TF, semantic inference, the live four-pane dashboard, Gazebo and RViz, and shutdown graph and mesh export remain pending inside that image. The recorded native launcher evidence in Part 1 includes 218 nodes, 624 edges, 95 PLACES nodes, both mesh files and Hydra exit 0. The user personally confirmed the native dashboard.

### Reproduction and publication

```bash
# These probes do not replace the CUDA requirement on the selected devel image.
docker run --rm --gpus all ros:jazzy-ros-base-noble nvidia-smi -L
docker run --rm --gpus all nvidia/cuda:12.6.3-base-ubuntu24.04@sha256:6b3201183858bad08441837f5a5efc2c75290135cc25fcc87d9ff763190cfd09 nvidia-smi -L

bash docker/build.sh
bash docker/build.sh --planning-only
HYDRA_ACRL_REFERENCE="$PWD/hydra_task_and_motion_planning/experiments/small_house/run_01" \
  bash docker/run.sh --planning python -B -I -m unittest discover -s tests -v
```

After the CUDA host gate passes, use the [Docker guide](../docker/README.md) for model preparation, full build and desktop/headless runs. The [publication inventory](PUBLICATION.md) records held files, licenses, the Git history review and the owner’s staging and publication commands. The local mapping target and any registry image have separate redistribution gates.

## Fresh-clone simplification

The current publication inventory supersedes the earlier bringup and Small House holds. The Waffle SDF and bridge were compared with ROBOTIS 2.3.7 under Apache-2.0. The bridge differs from the upstream bridge by its depth route. The world was compared with the AWS pinned release. The three files retained the same parsed configuration as the previously verified native installation after modification notices were added. The checkout now ships all 64 referenced AWS model directories and textures with the pinned AWS license. A separate isolated recovery from the AWS GitHub commit matched the checked-in model directories and license byte for byte.

Native setup automatically fetches Kimera-RPGO and restores an absent Small House bundle. The Docker build fetches the same Kimera revision in its build stage and takes the bringup code directly from the source context. Compose mounts the bundled 87,087,437-byte Small House directory rather than copying it into the image. The pinned Kimera-RPGO revision declares BSD but lacks its license text after the source-replacement commit `b148508`. Its source stays outside the Git inventory.

The model and folder links in the upstream semantic inference catalog returned HTTP 404. The verified ONNX checksum is retained. Native setup can compile without the model. The launcher checks the one user-supplied ONNX at run time. Both native and Docker launchers prompt if an engine already exists in an interactive terminal. The explicit flags remain available for automation.

The fresh native test copied only the proposed 1,928-file inventory into a temporary workspace. A mount namespace masked the original home, Windows drives and other temporary workspaces while retaining the installed OS toolchain and DNS. The test began without a model, overlays, a Python virtual environment or a local Kimera-RPGO tree. The CUDA Docker mapping image remains blocked by the host NVIDIA driver, and no rebuild was attempted. See the [publication inventory](PUBLICATION.md).

- **Static validation.** Bash syntax, launcher help, Compose rendering and Dockerfile mapping-target checks passed. A secret scan of the proposed tree and existing reachable Git history found no matches. None of the candidate paths were staged.
- **Fresh native build.** `bash hydra_mapping/setup.sh` downloaded the exact Kimera-RPGO revision and finished all 22 Hydra overlay packages in 26 minutes 22 seconds. The custom bringup package finished in a second. Colcon discovered all 23 packages, each had an install directory, and `ros2 pkg prefix` resolved `hydra_ros`, `hydra_visualizer`, `semantic_inference_ros` and `tb3_hydra_bringup` to the fresh overlays.
- **Fresh simulation.** A separately isolated `tb3_hydra_bringup` build used the bundled world with WSLg graphics. Gazebo found `hydra_waffle`. The native ROS probes received odometry in frame `odom`, RGB with encoding `rgb8` and the Hydra adapter's depth image with encoding `32FC1`.
- **Graph and mesh.** The fresh simulator probe used no ONNX. Semantic inference and Hydra were outside that probe, so it produced no graph or mesh. The native launcher exited at preflight with the expected model pathname and checksum. The checksum preflight also rejected a substitute file in isolation.
- **Planning.** `bash hydra_task_and_motion_planning/setup.sh --viz` built Spark-DSG 1.1.3 in a new Python 3.12 environment. `pip check` passed. The fresh environment and the existing CPU Docker image each saved and loaded a synthetic two-node PLACES graph and ran A*. Separately, all four native regressions passed again with the authorized historical fixture outside the isolated test.
- **Docker mapping.** The current checkout reached the CUDA preflight with 928 GiB of filesystem capacity reported inside Docker. Host driver 551.95 was rejected with `unsatisfied condition: cuda>=12.6`, and the script exited before compilation.
