import threading
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from pymodbus.server import StartTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext)

PREFIX = ""                                       # rebel.launch.py default prefix
JOINTS = [f"{PREFIX}joint{i}" for i in (1, 2, 3, 4)]   # -> joint1..joint4
N = len(JOINTS)

TRAJ_TOPIC  = "/joint_trajectory_controller/joint_trajectory"
STATE_TOPIC = "/joint_states"

SCALE = 1000.0            # radians * SCALE <-> Modbus INT (milliradians)
PORT = 1502
MOVE_TIME = 1.5          # seconds per move
TARGET_DEADBAND = 1e-3   # rad
REACHED_TOL = 0.04       # rad

FC_DISCRETE_INPUT = 2    # di: reached flag  (OpenPLC reads)
FC_READ_HOLDING = 3      # hr: joint targets (OpenPLC writes)
FC_WRITE_INPUT = 4       # ir: joint feedback(OpenPLC reads)


def to_signed(v):
    return v - 65536 if v > 32767 else v


def to_register(v):
    iv = max(-32768, min(32767, int(round(v))))
    return iv + 65536 if iv < 0 else iv


class OpenPLCBridge(Node):
    def __init__(self, ctx):
        super().__init__("openplc_rebel4dof_bridge")
        self.ctx = ctx
        self.last_target = None
        self.current = None
        self.pub = self.create_publisher(JointTrajectory, TRAJ_TOPIC, 10)
        self.create_subscription(JointState, STATE_TOPIC, self._on_state, 10)
        self.create_timer(0.1, self._on_timer)          # 10 Hz (matches CRI)
        self.get_logger().info(
            f"Modbus slave :{PORT} | joints={JOINTS} | pub={TRAJ_TOPIC}")

    def _on_state(self, msg):
        pos = dict(zip(msg.name, msg.position))
        if not all(j in pos for j in JOINTS):
            return
        self.current = [pos[j] for j in JOINTS]
        self.ctx[0].setValues(FC_WRITE_INPUT, 0,
                              [to_register(p * SCALE) for p in self.current])

    def _on_timer(self):
        raw = self.ctx[0].getValues(FC_READ_HOLDING, 0, count=N)
        target = [to_signed(v) / SCALE for v in raw]
        changed = (self.last_target is None or
                   any(abs(a - b) >= TARGET_DEADBAND
                       for a, b in zip(target, self.last_target)))
        if changed:
            traj = JointTrajectory()
            traj.joint_names = JOINTS
            pt = JointTrajectoryPoint()
            pt.positions = target
            pt.time_from_start = Duration(
                sec=int(MOVE_TIME),
                nanosec=int((MOVE_TIME - int(MOVE_TIME)) * 1e9))
            traj.points = [pt]
            self.pub.publish(traj)
            self.last_target = target
            self.get_logger().info(
                "cmd -> " + ", ".join(f"{x:+.2f}" for x in target))
        reached = (self.current is not None and self.last_target is not None and
                   all(abs(c - t) < REACHED_TOL
                       for c, t in zip(self.current, self.last_target)))
        #self.get_logger().info(f"reached={int(reached)} cur={self.current} tgt={self.last_target}")
        self.ctx[0].setValues(FC_DISCRETE_INPUT, 0, [1 if reached else 0])


def main():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 8),
        hr=ModbusSequentialDataBlock(0, [0] * 16),
        ir=ModbusSequentialDataBlock(0, [0] * 16),
        zero_mode=True)
    ctx = ModbusServerContext(slaves=store, single=True)
    rclpy.init()
    node = OpenPLCBridge(ctx)
    threading.Thread(target=StartTcpServer,
                     kwargs={"context": ctx, "address": ("0.0.0.0", PORT)},
                     daemon=True).start()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

