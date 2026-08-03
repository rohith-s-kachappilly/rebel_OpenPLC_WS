# rebel_ws

ROS 2 Humble workspace for the igus ReBeL 4-DOF hardware-in-the-loop testbed
at the Deutsche Telekom Chair of Communication Networks, TU Dresden.

## Packages

| Package | Origin | Purpose |
|---|---|---|
| `rebel_twin` | this repo | Gazebo Classic digital twin, `/sim` namespace, mirrors real `/joint_states` |
| `rebel_bridge` | this repo | OpenPLC <-> ROS 2 Modbus TCP bridge |
| `iRC_ROS` | vendored, **modified** | igus/CPR driver — see `docs/irc_ros_changes.md` |
| `ira_laser_tools`, `joint_state_publisher`, `rqt_robot_steering`, `sicks300_2` | vendored, unmodified | iRC_ROS dependencies |

Upstream origins and pinned commits: `docs/vendored_sources.txt`.
Third-party sources are vendored, not submoduled, because the driver requires
local fixes to run the packages in this workspace.

## Build

```bash
git clone git@github.com:TUDComnetsTSN/rebel_ws.git ~/rebel_ws
cd ~/rebel_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Run

```bash
ros2 launch rebel_twin <launch file>       # digital twin
ros2 launch rebel_bridge <launch file>     # OpenPLC bridge
```

## Requirements

- Ubuntu 22.04, ROS 2 Humble
- OpenPLC Runtime V3 (Modbus TCP)
- `pymodbus==3.6.9` (see `requirements.txt`)
