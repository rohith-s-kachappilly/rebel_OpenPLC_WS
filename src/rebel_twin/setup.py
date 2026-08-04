import os
from glob import glob
from setuptools import setup

package_name = "rebel_twin"


def recursive_data_files(src_dir, dest_root):
    """Mirror a directory tree into share/, preserving subdirectories.

    setuptools' data_files takes flat (dest_dir, [files]) pairs, so glob("models/*")
    only picks up the top level and drops everything nested. Gazebo models are
    directories (model.config, *.sdf, meshes/, materials/), so they need this.
    """
    out = []
    for path, _dirs, files in os.walk(src_dir):
        if not files:
            continue
        dest = os.path.join(dest_root, os.path.relpath(path, src_dir))
        out.append((dest, [os.path.join(path, f) for f in files]))
    return out


setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages",
            ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "urdf"),   glob("urdf/*")),
        (os.path.join("share", package_name, "config"), glob("config/*")),
        (os.path.join("share", package_name, "worlds"), glob("worlds/*.world")),
    ] + recursive_data_files("models", os.path.join("share", package_name, "models")),
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="tsn_lab",
    maintainer_email="tsn_lab@todo.todo",
    description="Gazebo digital twin for the igus ReBeL 4-DOF",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "mirror_node = rebel_twin.mirror_node:main",
        ],
    },
)
