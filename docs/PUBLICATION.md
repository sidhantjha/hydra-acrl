# Hydra-ACRL publication inventory

The source destination is [sidhantjha/hydra-acrl](https://github.com/sidhantjha/hydra-acrl). The working inventory is listed below. The repository owner retains the project licensing decision. There is no root project license in this change.

## In the source inventory

| Path | Content and attribution |
| --- | --- |
| Root docs and launcher, `docker/`, `Dockerfile`, `compose.yaml` | Project documentation, native launcher and local Docker tooling. |
| `hydra_mapping/hydra_ws/src/` | Ten vendored source trees with upstream license notices. Kimera-RPGO is fetched separately at build time. |
| `hydra_mapping/tb3_ws/src/tb3_hydra_bringup/` | The verified bridge, Waffle SDF, world, camera configuration, launches, adapters, relays and TF. The three derivatives carry modification notices and the package retains the AWS and ROBOTIS license and copyright files. |
| `hydra_mapping/small_house/` | The 64 world-referenced AWS model directories and required textures from the pinned revision, with its license. No upstream maps, routes or unrelated models are included. |
| `hydra_task_and_motion_planning/` | Source, packaging, scripts, historical notes and regression code. |
| `docs/`, `THIRD_PARTY_NOTICES.md`, `hydra_mapping/hydra.repos` and `patches/` | Reproduction evidence, pinned revisions, licensing and local modifications. |

The former local bridge, Waffle and world are included with comment-only attribution changes. The bridge matches ROBOTIS 2.3.7 with the additional depth route. The AWS project license accompanies the bundle and world derivative. [Third-party notices](../THIRD_PARTY_NOTICES.md)

## Outside the source inventory

| Input | Fresh-clone impact |
| --- | --- |
| Kimera-RPGO at `f1fee0900ef6825bf76304685668235cf5dd008d` | Native setup and the Docker build fetch it automatically for local compilation. The pinned commit declares BSD in `package.xml` and has no BSD text. The earlier `move rpgotools` commit removed the text while replacing the source. Permission to redistribute the pinned replacement remains unconfirmed. |
| `ade20k-efficientvit_seg_l2.onnx` and local TensorRT caches | The published model links failed during review. Supply an authorized ONNX at the documented path. The launcher checks its SHA256 and builds the engine locally. |
| Local reference DSG, plots, runtime graphs and other research outputs | CPU planning accepts a user-supplied DSG. The four historical regressions use the authorized local fixture. |
| Optional upstream dataset fixtures | The Spark-DSG apartment DSG and Matterport sample, semantic test media and CLIP pairs, and TEASER++ benchmark point clouds stay local. They are unnecessary for the maintained install and workflows. |
| Build outputs, virtual environments, archived scripts and unreviewed screenshots | Generated or local-only files. |

See the [quick start](../README.md#install-native-mapping) for the single model provisioning instruction and the [asset notes](../hydra_mapping/small_house/README.md) for how to regenerate the bundled assets.

## Local image and registry

The CUDA mapping image is intended for local builds on a compatible driver and will contain compiled Kimera-RPGO. Resolve its license and review the installed system, ROS, Python and NVIDIA binary terms before distributing an image. The CPU target has a separate binary inventory. The reserved registry destination is `ghcr.io/sidhantjha/hydra-acrl`. [CUDA EULA](https://docs.nvidia.com/cuda/eula/index.html) · [TensorRT SLA](https://docs.nvidia.com/deeplearning/tensorrt/latest/reference/sla.html)

## Inspect the staging set

```bash
git remote get-url release
git add --dry-run -A -- .gitignore .dockerignore .vscode AGENTS.md README.md \
  THIRD_PARTY_NOTICES.md Dockerfile compose.yaml docker docs launch.sh \
  hydra_mapping hydra_task_and_motion_planning src
```

The owner handles staging and publication. The audit and verification details are in the [implementation report](IMPLEMENTATION_REPORT.md).
