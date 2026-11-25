# syntax=docker/dockerfile:1
FROM ubuntu:24.04@sha256:9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a AS planning-build
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]
ENV MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1 LANG=C.UTF-8
RUN echo '[Hydra-ACRL] Planning system and Python dependencies' \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates cmake g++ git libeigen3-dev nlohmann-json3-dev python3-dev python3-venv \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/hydra-acrl
COPY hydra_mapping/hydra_ws/src/spark_dsg/ hydra_mapping/hydra_ws/src/spark_dsg/
COPY hydra_task_and_motion_planning/ hydra_task_and_motion_planning/
COPY hydra_mapping/scripts/export_dsg.* hydra_mapping/scripts/
COPY THIRD_PARTY_NOTICES.md ./
RUN --mount=type=cache,id=hydra-acrl-py312-pip,target=/root/.cache/pip,sharing=locked \
    echo '[Hydra-ACRL] Install Spark-DSG 1.1.3 and planning with visualization' \
    && bash hydra_task_and_motion_planning/setup.sh --viz \
    && hydra_task_and_motion_planning/.venv/bin/python -m pip check
FROM ubuntu:24.04@sha256:9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a AS planning
RUN echo '[Hydra-ACRL] Install CPU planning runtime' \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 libstdc++6 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/hydra-acrl
COPY --from=planning-build /opt/hydra-acrl/hydra_task_and_motion_planning/.venv/ hydra_task_and_motion_planning/.venv/
COPY hydra_task_and_motion_planning/scripts/ hydra_task_and_motion_planning/scripts/
COPY hydra_task_and_motion_planning/tests/test_reference.py hydra_task_and_motion_planning/tests/
COPY hydra_task_and_motion_planning/src/swarmx_planning/ hydra_task_and_motion_planning/src/swarmx_planning/
COPY hydra_mapping/scripts/export_dsg.* hydra_mapping/scripts/
COPY hydra_mapping/hydra_ws/src/spark_dsg/LICENSE licenses/Spark-DSG
COPY THIRD_PARTY_NOTICES.md ./
ENV PATH=/opt/hydra-acrl/hydra_task_and_motion_planning/.venv/bin:$PATH LANG=C.UTF-8
WORKDIR /opt/hydra-acrl/hydra_task_and_motion_planning
CMD ["bash"]

FROM nvidia/cuda:12.6.3-devel-ubuntu24.04@sha256:badf6c452e8b1efea49d0bb956bef78adcf60e7f87ac77333208205f00ac9ade AS mapping-deps
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]
ENV MAKEFLAGS=-j1 CMAKE_BUILD_PARALLEL_LEVEL=1 LANG=C.UTF-8 \
    CUDAToolkit_ROOT=/usr/local/cuda-12.6 TensorRT_ROOT=/usr
RUN echo '[Hydra-ACRL] Install compiler, native libraries and display tools' \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates curl git cmake build-essential pkg-config \
        python3-dev python3-venv python3-colcon-common-extensions \
        libboost-filesystem-dev libboost-system-dev libcli11-dev libeigen3-dev \
        libgflags-dev libgoogle-glog-dev libopencv-dev libpcl-dev libyaml-cpp-dev libzmq3-dev \
        nlohmann-json3-dev pybind11-dev python3-flask python3-numpy \
        libegl1 libgl1-mesa-dri libglx-mesa0 mesa-utils tmux \
    && rm -rf /var/lib/apt/lists/*
RUN echo '[Hydra-ACRL] Install exact TensorRT 10.4 packages' \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        libnvinfer10=10.4.0.26-1+cuda12.6 \
        libnvinfer-headers-dev=10.4.0.26-1+cuda12.6 \
        libnvinfer-dev=10.4.0.26-1+cuda12.6 \
        libnvinfer-plugin10=10.4.0.26-1+cuda12.6 \
        libnvinfer-headers-plugin-dev=10.4.0.26-1+cuda12.6 \
        libnvinfer-plugin-dev=10.4.0.26-1+cuda12.6 \
        libnvonnxparsers10=10.4.0.26-1+cuda12.6 \
        libnvonnxparsers-dev=10.4.0.26-1+cuda12.6 \
    && rm -rf /var/lib/apt/lists/*
RUN echo '[Hydra-ACRL] Install ROS 2 Jazzy, Gazebo Harmonic, RViz and TurtleBot3' \
    && curl --fail --location --retry 3 \
        https://github.com/ros-infrastructure/ros-apt-source/releases/download/1.3.0/ros2-apt-source_1.3.0.noble_all.deb \
        -o /tmp/ros2-apt-source.deb \
    && echo 'f31d84adf5054c7d60ded0e82c0f776a77ea33af53d08f40b9ad7c94cca55296  /tmp/ros2-apt-source.deb' | sha256sum -c - \
    && dpkg -i /tmp/ros2-apt-source.deb \
    && rm /tmp/ros2-apt-source.deb \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ros-jazzy-ros-base ros-jazzy-rosidl-default-generators ros-jazzy-ros-gz \
        ros-jazzy-cv-bridge ros-jazzy-image-geometry ros-jazzy-image-transport-plugins \
        ros-jazzy-gtsam ros-jazzy-interactive-markers ros-jazzy-rosbag2 \
        ros-jazzy-rviz2 ros-jazzy-tf2-eigen ros-jazzy-topic-tools \
        ros-jazzy-turtlebot3-gazebo ros-jazzy-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/hydra-acrl

# The mapping image is for local use. Fetch the pinned dependency at build time.
FROM mapping-deps AS mapping-build
COPY docker/build.sh docker/build.sh
COPY hydra_mapping/hydra_ws/ hydra_mapping/hydra_ws/
COPY hydra_mapping/scripts/prepare_external.sh hydra_mapping/scripts/
RUN bash hydra_mapping/scripts/prepare_external.sh rpgo
# Wait for the Spark-DSG wheel so its compiler cannot overlap with colcon.
RUN --mount=type=bind,from=planning,source=/opt/hydra-acrl/hydra_task_and_motion_planning/.venv,target=/tmp/planning-venv \
    --mount=type=cache,id=hydra-acrl-jazzy-cu126-hydra-build,target=/opt/hydra-acrl/hydra_mapping/hydra_ws/build,sharing=locked \
    test -x /tmp/planning-venv/bin/python && bash docker/build.sh _compile hydra_ws
COPY hydra_mapping/tb3_ws/ hydra_mapping/tb3_ws/
RUN --mount=type=cache,id=hydra-acrl-jazzy-cu126-bringup-build,target=/opt/hydra-acrl/hydra_mapping/tb3_ws/build,sharing=locked \
    bash docker/build.sh _compile tb3_ws

FROM mapping-deps AS mapping
LABEL org.opencontainers.image.title="Hydra-ACRL (local mapping and planning)" \
      org.opencontainers.image.source="https://github.com/sidhantjha/hydra-acrl" \
      org.opencontainers.image.version="1.0.0"
COPY --from=mapping-build /opt/hydra-acrl/hydra_mapping/hydra_ws/install/ hydra_mapping/hydra_ws/install/
COPY --from=mapping-build /opt/hydra-acrl/hydra_mapping/tb3_ws/install/ hydra_mapping/tb3_ws/install/
COPY --from=planning /opt/hydra-acrl/hydra_task_and_motion_planning/ hydra_task_and_motion_planning/
COPY --from=planning /opt/hydra-acrl/licenses/ licenses/
COPY launch.sh THIRD_PARTY_NOTICES.md ./
COPY hydra_mapping/hydra.repos hydra_mapping/
COPY hydra_mapping/scripts/run_mapping.sh hydra_mapping/scripts/mapping_environment.sh hydra_mapping/scripts/export_dsg.sh hydra_mapping/scripts/export_dsg.py hydra_mapping/scripts/
COPY docker/entrypoint.sh /usr/local/bin/hydra-acrl-entrypoint
ENV QT_X11_NO_MITSHM=1
ENTRYPOINT ["/usr/local/bin/hydra-acrl-entrypoint"]
CMD ["dashboard"]
