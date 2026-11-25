# Hydra-ACRL architecture

```text
Gazebo Small House and Hydra Waffle
  → ROS bridges → RGB/depth adapter, odometry and TF
  → EfficientViT ADE20K and Hydra → live DSG → streaming visualizer → RViz
                              ↓
                      shutdown save and export
                              ↓
            Spark-DSG JSON → PLACES extraction → CPU route experiments
```

The [Hydra overlay](../hydra_mapping/hydra_ws/src/) contains Hydra, Hydra-ROS, Spark-DSG, semantic inference, Kimera and supporting dependencies. [hydra.repos](../hydra_mapping/hydra.repos) records their source revisions. The [TurtleBot3 overlay](../hydra_mapping/tb3_ws/src/tb3_hydra_bringup/) owns the robot and Small House simulation integration. Its [launch files](../hydra_mapping/tb3_ws/src/tb3_hydra_bringup/launch/) load the world, spawn the Waffle, start bridges and adapters and connect the existing visualizer. Its [configuration](../hydra_mapping/tb3_ws/src/tb3_hydra_bringup/config/) controls bridge types, Hydra input and mapping parameters.

[launch.sh](../launch.sh) selects a Gazebo partition, starts the mapping runner in a tmux pane and checks the entity, velocity bridge and odometry before enabling interactive drive. Gazebo's GUI attaches after spawn. The streaming visualizer subscribes to `/hydra/backend/dsg`. Each run records startup details and logs. The [exporter](../hydra_mapping/scripts/export_dsg.sh) checks Hydra’s exit and graph, then records the mesh artifacts independently.

The [planning module](../hydra_task_and_motion_planning/) consumes the exported graph through its standalone Python environment and the vendored Spark-DSG binding. The reusable planner uses XYZ distance, the Small House experiments use XY distance and a vertical-edge filter, and the animations use NetworkX weighted shortest paths. The [experimental waypoint controller](../hydra_task_and_motion_planning/src/swarmx_planning/control/) lives in planning and uses the velocity infrastructure supplied by `tb3_ws`. It uses preset waypoints and consumes no DSG route.

The intended GitHub publication destination is [sidhantjha/hydra-acrl](https://github.com/sidhantjha/hydra-acrl). For future container work, reserve `hydra-acrl:latest`, `hydra-acrl:1.0.0` and `ghcr.io/sidhantjha/hydra-acrl`. Existing package and checkout names remain the runtime identifiers.
