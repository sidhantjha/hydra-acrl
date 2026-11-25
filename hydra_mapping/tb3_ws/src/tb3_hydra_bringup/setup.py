import os
from glob import glob
from setuptools import find_packages, setup

package_name = "tb3_hydra_bringup"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
        (os.path.join("share", package_name, "worlds"), glob("worlds/*.world")),
        (os.path.join("share", package_name, "models", "hydra_waffle"),
         glob("models/hydra_waffle/*")),
        (os.path.join("share", package_name, "notices"), glob("notices/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="swarmx",
    maintainer_email="sidhantjha373@gmail.com",
    description="Hydra-ACRL TurtleBot3 ROS 2 bringup package",
    license="Project license pending confirmation",
    extras_require={
        "test": ["pytest"],
    },
    entry_points={
        "console_scripts": [
            "image_adaptor = tb3_hydra_bringup.nodes.image_adaptor:main",
            'image_adaptor_semantic = tb3_hydra_bringup.nodes.image_adaptor_semantic:main',
        ],
    },
)
