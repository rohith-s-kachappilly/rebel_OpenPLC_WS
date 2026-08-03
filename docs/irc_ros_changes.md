# Local changes to iRC_ROS

Vendored from https://github.com/CommonplaceRobotics/iRC_ROS
branch `humble`, commit `41701e6df3398087d217f0f478622e60f694de41`.

All modifications are isolated in a single commit; see `git log -- src/iRC_ROS`.
A standalone diff is kept at `patches/iRC_ROS.diff`.

## 1. `irc_ros_hardware/src/irc_ros_cri.cpp`

The read path applied `cri_joint_offset` with the same sign as the write path,
so `/joint_states` reported twice the offset. Changed to subtract.

## 2. `irc_ros_bringup/launch/rebel.launch.py`

Commented out `description.add_action(joint_state_pub)`. `joint_state_publisher`
was a second publisher on `/joint_states` while also self-subscribing via
`source_list`, which fought with the hardware interface.

## 3. `irc_ros_hardware/src/CRI/cri_socket.cpp`

`SeparateMessages` segfaulted in `strstr` on a null pointer when a fragmented
robot message could not be reassembled. Added a null guard, `end = msg`
recovery, a `bufferSize - 1` read, and `fragmentBuffer.data()` in place of
`.front()`.

## 4. `irc_ros_bringup/config/controller_igus_rebel_4dof.yaml`

TODO: describe what changed and why.

## Re-syncing onto a newer upstream

Clone upstream fresh at the target commit, apply `patches/iRC_ROS.diff`,
resolve conflicts, and replace `src/iRC_ROS/` in one commit.
