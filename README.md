# IGUS_REBEL_4DOF_01(24V) Integration with OpenPLC

ROS 2 Humble workspace for the igus ReBeL 4-DOF hardware-in-the-loop testbed
at the Deutsche Telekom Chair of Communication Networks, TU Dresden.

## System Architecture
<img width="1800" height="1650" alt="openplc_ros2_rebel_twin_interface_map" src="https://github.com/user-attachments/assets/b0358af9-d98e-47e8-84d7-f151777a97fe" />


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
git clone git@github.com:rohith-s-kachappilly/rebel_OpenPLC_WS.git ~/rebel_ws
cd ~/rebel_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```
**NOTE:** Use only symlink install to build the packages.

## Run

```bash
ros2 launch rebel_twin digital_twin_launch.py       # digital twin
ros2 run rebel_bridge openplc_bridge.py             # OpenPLC bridge
```

## Requirements

Everything needed to build and run the OpenPLC → igus ReBeL 4-DOF → Gazebo digital twin
testbed in `~/rebel_ws`.

---

### Host system

| | |
|---|---|
| OS | Ubuntu 22.04 (Jammy) |
| ROS 2 | Humble Hawksbill |
| Simulator | Gazebo Classic 11 |
| Python | 3.10 (Ubuntu default) |
| Network | Ethernet NIC on the robot subnet, `192.168.3.0/24` |

Gazebo Classic, not Ignition/Gazebo Sim — the twin uses `gazebo_ros2_control` and
`libgazebo_ros2_control.so`, which are Classic-only.

---

### ROS 2 packages

```bash
sudo apt update
sudo apt install -y \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-controller-manager \
  ros-humble-joint-state-broadcaster \
  ros-humble-joint-trajectory-controller \
  ros-humble-position-controllers \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-xacro \
  ros-humble-nav2-common \
  python3-colcon-common-extensions python3-vcstool python3-rosdep
```

What each is actually for:

- `joint-trajectory-controller` — drives the **real** arm; the bridge publishes to it
- `position-controllers` — provides `JointGroupPositionController` for the **twin**
- `gazebo-ros2-control` — the `libgazebo_ros2_control.so` plugin the twin's xacro loads
- `nav2-common` — `rebel.launch.py` imports `ReplaceString` from it

---

### Python packages

```bash
pip install "pymodbus==3.6.9" --break-system-packages
```

**Pin this exact version.** pymodbus 3.7+ changed the datastore and server API; the
bridge's `ModbusSlaveContext` / `StartTcpServer` usage will not run on it.

---

### OpenPLC Runtime

OpenPLC Runtime V4, running as Modbus TCP **master**. The bridge is the slave.

Required settings:

- **Settings → Enable Modbus Server: OFF.** OpenPLC's own server would clash with the
  bridge on the port.
- **Slave Devices → one** Generic Modbus TCP device at `127.0.0.1:1502`.
  One device, not one per joint.

---

### Robot hardware

| | |
|---|---|
| Arm | igus ReBeL 4-DOF, **revision 01** |
| Interface | CRI over Ethernet |
| Robot IP | `192.168.3.11` (default, set in `igus_rebel_4dof_00.ros2_control.xacro`) |
| PC IP | `192.168.3.10/24` |

```bash
sudo ip addr add 192.168.3.10/24 dev <nic>
sudo ip link set <nic> up
ping 192.168.3.11
```

The launch file defaults `hardware_protocol` to `cprcanv2` (CAN) — **`cri` must be passed
explicitly** for the Ethernet arm.

