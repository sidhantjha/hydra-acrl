# Small House Run 01

## Gazebo spawn

- x: -3.6655 m
- y: -0.4874 m
- z: 0.0 m
- yaw: 0 rad

## Hydra map convention

Odometry initializes at the robot spawn pose and `world -> odom` is identity.

Therefore the robot begins the Hydra map approximately at:

- x: 0.0 m
- y: 0.0 m
- yaw: 0 rad

After the mature DSG is generated, the planning start node should be selected as the PLACES node nearest the Hydra map origin.

## Environment

- AWS RoboMaker Small House
- Ceiling enabled
- Depth validity at initial pose: 90.72%
- Depth: 720x480, 32FC1
