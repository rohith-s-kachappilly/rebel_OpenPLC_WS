#!/usr/bin/env python3
"""Digital-twin mirror: real ReBeL /joint_states -> Gazebo twin. One direction only."""
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray

REAL_JOINTS = ["joint1", "joint2", "joint3", "joint4"]   # real arm, default prefix
SIM_CMD_TOPIC = "/sim/arm_position_controller/commands"
# rad. j2/j3 = -30 deg, j4 = -7.5 deg. Flip the signs if the twin's error doubles.
#DEFAULT_OFFSETS = [0.0, -0.9599310885968813, -1.3962634015954636, -0.1308996938995747]   # rad, from the twin's URDF
SIGNS = [-1.0, 1.0, 1.0, 1.0]   # joint1 axis is reversed in the twin
DEFAULT_OFFSETS = [0.0, -1.0471975511965976, -1.0471975511965976, 0.2617993877991494]
class Mirror(Node):
    def __init__(self):
        super().__init__("rebel_twin_mirror")
        self.declare_parameter("joint_offsets", DEFAULT_OFFSETS)
        self.offsets = list(
            self.get_parameter("joint_offsets").get_parameter_value().double_array_value)
        if len(self.offsets) != len(REAL_JOINTS):
            self.offsets = list(DEFAULT_OFFSETS)
        self.add_on_set_parameters_callback(self._on_param)
        self.get_logger().info(f"joint_offsets (rad) = {self.offsets}")
        self.pub = self.create_publisher(Float64MultiArray, SIM_CMD_TOPIC, 10)
        self.create_subscription(JointState, "/joint_states", self._cb, 10)
        self.get_logger().info("Mirror: real /joint_states -> " + SIM_CMD_TOPIC)

    def _on_param(self, params):
        for p in params:
            if p.name == "joint_offsets":
                if len(p.value) != len(REAL_JOINTS):
                    return SetParametersResult(
                        successful=False,
                        reason=f"joint_offsets needs exactly {len(REAL_JOINTS)} values")
                self.offsets = list(p.value)
                self.get_logger().info(f"joint_offsets updated -> {self.offsets}")
        return SetParametersResult(successful=True)

    def _cb(self, msg):
        pos = dict(zip(msg.name, msg.position))
        if not all(j in pos for j in REAL_JOINTS):
            return
        out = Float64MultiArray()
        # order == sim controller joint order
        out.data = [pos[j]*s + o for j, s, o in zip(REAL_JOINTS, SIGNS, self.offsets)]
        self.pub.publish(out)

def main():
    rclpy.init()
    node = Mirror()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
