# Local changes to iRC_ROS

Vendored from https://github.com/CommonplaceRobotics/iRC_ROS
branch `humble`, commit `41701e6df3398087d217f0f478622e60f694de41`.

All modifications are isolated in a single commit; see `git log -- src/iRC_ROS`.
A standalone diff is kept at `patches/iRC_ROS.diff`.

# Local changes to iRC_ROS

Modifications made to the vendored `CommonplaceRobotics/iRC_ROS` clone (`humble` branch)
in `~/rebel_ws/src/iRC_ROS`. These are **not** upstream — a `git pull` will discard them.

Keep the generated patch alongside this file:

```bash
cd ~/rebel_ws/src/iRC_ROS && git diff > ~/rebel_ws/irc_ros_local_patches.diff
```

Four files are modified. Of the five vendored repos in the workspace (`iRC_ROS`,
`ira_laser_tools`, `joint_state_publisher`, `rqt_robot_steering`, `sicks300_2`), only
`iRC_ROS` carries local edits.

---

## 1. `irc_ros_hardware/src/irc_ros_cri.cpp` — joint offset applied twice

**Symptom.** `/joint_states` reported roughly double the `cri_joint_offset` on every
offset joint: ~60° on joint2 and joint3, ~15° on joint4. Command and feedback never
agreed, so the `reached` comparison in the OpenPLC bridge could not be satisfied at any
sane tolerance and the PLC sequence deadlocked on its first pose.

**Cause.** The write path (line 286) adds the offset:

```cpp
msg << (set_pos_[i] * 180 / M_PI) + pos_offset_[i] << " ";
```

The read path (line 469) added it a second time instead of inverting it.

**Change.** Line 469:

```diff
-    temp_pos[i] = temp_pos[i] + pos_offset_[i];
+    temp_pos[i] = temp_pos[i] - pos_offset_[i];
```

**Verification.** Commanding `[0, 0, 0, 0]` returns `[0, 0, 0, 0]`; commanding
`[0, 0.8, 0.8, 0.3]` returns within 0.6 mrad. Both well inside `REACHED_TOL = 0.04`.

---

## 2. `irc_ros_hardware/src/CRI/cri_socket.cpp` — segfault in `SeparateMessages`

**Symptom.** `ros2_control_node` died with `Segmentation fault (Address not mapped to
object (nil))`, stack ending in `CriSocket::SeparateMessages` → `__strstr_sse2_unaligned`.
Immediately preceded in the log by:

```
There was a partial robot message, but could not find the end of it in the next message.
Unknown message type: "VARIABLES"
Unknown message type: "LOGMSG"
```

**Cause.** When a fragment could not be reassembled, the error branch logged and fell
through with `end` still `nullptr`, straight into `strstr(end, ...)` in the loop below.

Three edits, all inside `SeparateMessages` / `ReceiveThreadFunction`:

### 2a. Recover instead of falling through with a null pointer

```diff
       RCLCPP_ERROR(
         rclcpp::get_logger("iRC_ROS::CRI"),
         "There was a partial robot message, but could not find the end of it in the next message.");
+      end = msg;
     } else {
```

Discards the broken fragment and rescans the buffer from the start.

### 2b. Fix the reassembly (upstream `TODO`)

```diff
-      std::string result1(fragmentBuffer.front(), fragmentLength);
+      std::string result1(fragmentBuffer.data(), fragmentLength);
```

`fragmentBuffer` is a `std::array<char, bufferSize>`, so `front()` returns a **char**.
That selected `std::string(size_type count, char ch)` — building a string whose *length*
was the numeric value of the first buffered byte, filled with `char(fragmentLength)`.
Every reassembled fragment came out as garbage, which is the likely source of the
unknown-message-type errors that triggered the crash in the first place.

### 2c. Guarantee null termination

```diff
-    int valread = read(sock, buffer, bufferSize);
+    int valread = read(sock, buffer, bufferSize - 1);
```

A full-length read left no terminator, so `strstr` could walk past the end of the buffer.

> **Note.** An earlier attempt at these edits accidentally deleted the `CriSocket`
> constructor definition. Shared libraries permit undefined symbols at link time, so
> `colcon build` reported success and the failure only appeared at launch as
> `undefined symbol: _ZN12irc_hardware9CriSocketC1E...` with exit code 127.
> Check after every C++ edit:
>
> ```bash
> nm -C ~/rebel_ws/install/irc_ros_hardware/lib/libirc_ros_hardware.so | grep " U irc_hardware"
> ```
>
> Empty output is correct. Undefined `std::` / `rclcpp::` symbols are normal.

---

## 3. `irc_ros_bringup/launch/rebel.launch.py` — duplicate `/joint_states` publisher

**Symptom.** `ros2 topic info /joint_states` reported `Publisher count: 2`. Messages
alternated between two sources with different joint orderings and different `frame_id`
values, so `self.current` in the bridge flipped between real positions and defaults, and
`reached` could never hold true for the consecutive scans the OpenPLC dwell requires.

**Cause.** `rebel.launch.py` starts a `joint_state_publisher` alongside the
`joint_state_broadcaster`. With `namespace=""` it both subscribes to and publishes on
`/joint_states` (via `source_list`), and fills `0.0` for any joint it has no data for.

**Change.** Under `# Robot nodes`:

```diff
     description.add_action(robot_state_pub)
-    description.add_action(joint_state_pub)
+    # description.add_action(joint_state_pub)   # duplicate /joint_states publisher
```

The `joint_state_pub = Node(...)` definition is left in place — an unused variable keeps
the patch small and easy to re-apply.

---

## 4. `irc_ros_bringup/config/controller_igus_rebel_4dof.yaml`

**Change.** Configured the update rate of ros_parameters from 100 Hz to 10 Hz for the CRI interface.


## Rebuilding

```bash
cd ~/rebel_ws
colcon build --packages-select irc_ros_hardware irc_ros_bringup
source install/setup.bash
```

`irc_ros_hardware` is C++ — `--symlink-install` does not apply, every edit needs a rebuild.
Restart any running launch afterwards; the old binary stays loaded until you do.

---

## Open items

- **Hardware revision mismatch.** The physical arm is revision **01**, but
  `rebel_twin`'s xacro includes `igus_rebel_4dof_00.description.xacro`, and the
  `cri_joint_offset` values reasoned about above (`-30 / -30 / +7.5`) come from
  `igus_rebel_4dof_00.ros2_control.xacro`. This is the standing suspect for the residual
  RViz and Gazebo pose discrepancy — including joint1 needing a **sign flip** in the
  mirror node, which no offset can account for.
- **Upstream reporting.** Items 1 and 2 are unambiguous upstream bugs with small fixes.
  Worth filing against `CommonplaceRobotics/iRC_ROS` with the stack trace, and worth
  checking first whether a newer branch already addresses the V14/V15 CRI protocol
  messages (`VARIABLES`, `LOGMSG`) that the humble driver does not parse.

## Re-syncing onto a newer upstream

Clone upstream fresh at the target commit, apply `patches/iRC_ROS.diff`,
resolve conflicts, and replace `src/iRC_ROS/` in one commit.
