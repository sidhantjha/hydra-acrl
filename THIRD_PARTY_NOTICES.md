# Hydra-ACRL third-party notices

Upstream URLs and verified local HEADs are recorded in [hydra.repos](hydra_mapping/hydra.repos). License paths are relative to each dependency root in `hydra_mapping/hydra_ws/src`. The working-tree changes in Hydra and Hydra-ROS are recorded as audit patches under `hydra_mapping/patches/`.

| Dependency and upstream | Original commit | License and notice | Audited local changes | Consolidation and review |
| --- | --- | --- | --- | --- |
| [hydra](https://github.com/MIT-SPARK/Hydra.git) | `654c3303e1ad64031759ef230d9aec024c11fb99` | BSD-3-Clause, `LICENSE` | Spatial radius 8 → 25 m | Restored upstream YAML and carried 25 m in bringup config. Pinned nanoflann. Omitted large overview GIF. |
| [hydra_ros](https://github.com/MIT-SPARK/Hydra-ROS.git) | `f95e3c7f1473b14f570378d7d2350c8848ef6cc6` | BSD-3-Clause, `LICENSE` | Depth range 5 → 10 m, disabled dataset inference include, added world-to-map TF, changed generic frame defaults, emptied OAK-D config | Restored four upstream YAMLs. The Small House launch owns inference and world-to-map TF and sets frames explicitly. Bringup input YAML carries the 10 m range. |
| [spark_dsg](https://github.com/MIT-SPARK/Spark-DSG.git) | `be110f394bbc6d74e0390f77d41b11aae175fd0c` | BSD-3-Clause, `LICENSE` | None observed | Builds as a standalone Python binding for planning. |
| [semantic_inference](https://github.com/MIT-SPARK/semantic_inference.git) | `d8ca2e60ca7b872aea73fd28be37b1a3b919eab8` | BSD-3-Clause, `LICENSE; semantic_inference_ros/LICENSE` | None observed | Omitted the nested Mask2Former gitlink and .gitmodules. |
| [config_utilities](https://github.com/MIT-SPARK/config_utilities.git) | `2e53b6d8d9d908d06cf172741346806d9f664cf8` | BSD-3-Clause, `LICENSE; config_utilities_{ros,msgs}/LICENSE` | None observed | Source unchanged. |
| [spatial_hash](https://github.com/MIT-SPARK/Spatial-Hash.git) | `8045892f34978d78870d806a50f8e5aefdbe52fc` | BSD-3-Clause, `LICENSE` | None observed | Source unchanged. |
| [ianvs](https://github.com/MIT-SPARK/Ianvs.git) | `a4fb1cb78774df3adfd8bb541d55d8d85556b471` | MIT, `LICENSE` | None observed | Source unchanged. |
| [kimera_pgmo](https://github.com/MIT-SPARK/Kimera-PGMO.git) | `dcf948b8d8f34a45ec59e5c09d54213dc28764d1` | BSD-3-Clause, `LICENSE` | None observed | Source unchanged. Happly carries its own notice in its source. |
| [kimera_rpgo](https://github.com/MIT-SPARK/Kimera-RPGO.git) | `f1fee0900ef6825bf76304685668235cf5dd008d` | BSD declared, `package.xml; referenced LICENSE absent` | None observed | Setup fetches the pinned source for local builds. The pinned revision lacks the BSD text. The preceding source migration removed it, so permission for redistribution of the replacement source remains unconfirmed. |
| [pose_graph_tools](https://github.com/MIT-SPARK/pose_graph_tools.git) | `965dfe864487be9040195c598fd89718563c348c` | BSD-3-Clause, `LICENSE.BSD` | None observed | Source unchanged. |
| [teaser_plusplus](https://github.com/MIT-SPARK/TEASER-plusplus.git) | `e2f6f17bb610f06b5236b18cfbd38333802d9b6b` | MIT, `LICENSE` | None observed | Pinned pmc, tinyply and test googletest. Omitted examples and test point-cloud data. Legacy Conda recipe separately labels its binding GPL3. |

The retained source trees include their upstream license notices. Review the ancillary TEASER++ Conda recipe terms before redistributing a build of that binding. Hydra's optional LCD model files under `models/lcd` follow the upstream ignore rule and remain local. The small upstream unit-test ONNX fixtures are included as source resources. The optional segmentation zoo's [Mask2Former](https://github.com/facebookresearch/Mask2Former.git) reference at `9b0651c6c1d5b3af2e6da0589b719c514ec0d69a` is outside the packaged inference path.

## Downloads at build time

| Dependency | Repository | Audited revision and integration |
| --- | --- | --- |
| nanoflann | [jlblancoc/nanoflann](https://github.com/jlblancoc/nanoflann) | `9a653cb243db6a09c94f833b28732b62f033e2b5`, Hydra changed from v1.7.1 to its commit |
| spectra | [jingnanshi/spectra](https://github.com/jingnanshi/spectra) | `5c4fb1de050847988faaaaa50f60e7d3d5f16143`, existing TEASER++ pin |
| pmc | [jingnanshi/pmc](https://github.com/jingnanshi/pmc) | `a2dfd612a501bca83c47206255dbbff619481f97`, pinned in TEASER++ |
| tinyply | [ddiakopoulos/tinyply](https://github.com/ddiakopoulos/tinyply) | `4495bb5757346f60f9910b8fcf848c878a8d54aa`, pinned in TEASER++ |
| googletest | [google/googletest](https://github.com/google/googletest) | `5a9c3f9e8d9b90bbbe8feb32902146cb8f7c1757`, pinned in optional TEASER++ tests, disabled by mapping setup |

The Spark-DSG CMake fallback can download nlohmann/json v3.11.3 and the checksum-checked Eigen 3.4.0 archive when find-package fallback is enabled. Python setup obtains Python build and runtime dependencies through pip. Optional Hydra GNN code can download ONNX Runtime v1.13.1 for Linux x64 with GPU. An unused TEASER++ helper references pybind11 v2.13.6, and the standalone happly test template references floating googletest master. These optional builds are outside the default workflow.

## Simulation, models and data

- The repository bundles the 64 world-referenced AWS model directories and required textures from [AWS RoboMaker Small House at ff9631c](https://github.com/aws-robotics/aws-robomaker-small-house-world/tree/ff9631ca6d1db9c1ba656498151464b5ab74aafe). The pinned project license permits redistribution with its copyright and permission notice. An exact copy is in [the asset directory](hydra_mapping/small_house/LICENSE) and the bringup notices. The world derivative adapts the original Gazebo world to Harmonic plugins and enables the ceiling. Local asset changes are limited to the ShoeRack typo and Collada portrait path resolution using the pinned JPEGs.
- The custom Waffle and bridge derive from [ROBOTIS turtlebot3_simulations 2.3.7](https://github.com/ROBOTIS-GIT/turtlebot3_simulations/tree/9be186fb03d84ed4f293e5c0db71d8c05bbc91f3). The bridge appends a depth topic to the upstream YAML. The Waffle reuses the stock chassis, dynamics and sensor configuration with modifications for RGB-D mapping, frame IDs and model resource paths. Prominent modification comments identify the derivatives. The bringup package retains the stock copyright notice and the upstream Apache-2.0 text. Robot meshes are supplied by the installed ROBOTIS ROS package.
- The EfficientViT ADE20K model and TensorRT engine are supplied locally. The [MIT SPARK model catalog](hydra_mapping/hydra_ws/src/semantic_inference/docs/closed_set.md#models) identifies its preferred pre-exported model. Its model and folder links returned HTTP 404 during the fresh-clone review. The SHA256 of the verified artifact is recorded in the quick start. Upstream software licensing does not establish model weight distribution terms.
- The local baseline graph, sweep CSV and figures remain excluded pending data provenance and publication review. No root project license has been selected.
