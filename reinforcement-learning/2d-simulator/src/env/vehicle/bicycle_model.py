"""Bicycle Modelの物理計算"""

from Box2D import b2Vec2, b2Body
import numpy as np
from typing import Dict, Optional

from src.env.vehicle.config import VehicleConfig


class BicycleModelController:
    """Bicycle Modelの物理計算を担当

    タイヤ摩擦、駆動力、角速度減衰、横滑り抑制などの
    Bicycle Model特有の物理計算を実行する。
    """

    def __init__(
        self,
        config: VehicleConfig,
        max_motor_force: float = 20.0,
        max_lateral_impulse: float = 2.5,
    ):
        """
        Args:
            config: 車両設定
            max_motor_force: 最大モーター力 (N)
            max_lateral_impulse: 最大横滑りインパルス
        """
        self.config = config
        self.max_motor_force = max_motor_force
        self.max_lateral_impulse = max_lateral_impulse

    def apply_control(
        self,
        body: b2Body,
        steering: float,
        throttle: float,
        debug: bool = False
    ):
        """制御入力を適用（Bicycle Modelベース）

        Args:
            body: Box2Dのボディ
            steering: 正規化されたステアリング入力 (-1.0 ~ 1.0)
            throttle: 正規化されたスロットル入力 (-1.0 ~ 1.0)
            debug: デバッグ情報を出力するか
        """
        # ステアリング角度を計算
        steer_angle = -steering * self.config.max_steering_angle

        if debug:
            print(f"[DEBUG] Steering: {steering:.4f}, Throttle: {throttle:.4f}")
            print(f"[DEBUG] Body angle: {body.angle:.4f}, Angular velocity: {body.angularVelocity:.4f}")

        # ホイール位置の計算
        wheel_positions = self._compute_wheel_positions(body)

        # 各サブシステムに制御を委譲
        self._apply_tire_friction(body, steer_angle, wheel_positions, debug=debug)
        self._apply_drive_force(body, steer_angle, throttle, wheel_positions)
        self._apply_angular_damping(body, steering)

    def _compute_wheel_positions(self, body: b2Body) -> Dict:
        """前輪と後輪のワールド座標位置を計算"""
        front_local = b2Vec2(self.config.wheelbase / 2, 0)
        rear_local = b2Vec2(-self.config.wheelbase / 2, 0)

        front_world = body.GetWorldPoint(front_local)
        rear_world = body.GetWorldPoint(rear_local)

        return {
            "front_local": front_local,
            "rear_local": rear_local,
            "front_world": front_world,
            "rear_world": rear_world,
        }

    def _apply_tire_friction(
        self,
        body: b2Body,
        steer_angle: float,
        wheel_positions: Dict,
        debug: bool = False
    ):
        """タイヤの横滑りを抑制"""
        threshold = self.config.control_params.steering_threshold_straight

        if abs(steer_angle) < threshold:
            # 完全に真っ直ぐ進む時は、重心で横滑りを抑制
            self._kill_lateral_velocity(body, body.angle, world_point=None, debug=debug)
        else:
            # ステアリングがある時は各ホイールで抑制
            front_wheel_angle = body.angle + steer_angle
            rear_wheel_angle = body.angle

            self._kill_lateral_velocity(
                body, front_wheel_angle, wheel_positions["front_world"], debug=debug
            )
            self._kill_lateral_velocity(
                body, rear_wheel_angle, wheel_positions["rear_world"], debug=debug
            )

    def _apply_drive_force(
        self,
        body: b2Body,
        steer_angle: float,
        throttle: float,
        wheel_positions: Dict
    ):
        """駆動力を適用"""
        threshold = self.config.control_params.steering_threshold_straight

        if abs(steer_angle) < threshold:
            # 真っ直ぐ進む時は車体の向きで重心に適用
            direction = b2Vec2(np.cos(body.angle), np.sin(body.angle))
            force = throttle * self.max_motor_force * direction
            body.ApplyForce(force, body.worldCenter, True)
        else:
            # ステアリングがある時は前輪位置に適用
            front_wheel_angle = body.angle + steer_angle
            direction = b2Vec2(np.cos(front_wheel_angle), np.sin(front_wheel_angle))
            force = throttle * self.max_motor_force * direction
            body.ApplyForce(force, wheel_positions["front_world"], True)

    def _apply_angular_damping(self, body: b2Body, steering: float):
        """角速度の減衰を適用"""
        threshold = self.config.control_params.steering_threshold_damping

        if abs(steering) < threshold:
            damping = self.config.control_params.angular_damping_strong
        else:
            damping = self.config.control_params.angular_damping_normal

        angular_impulse = -damping * body.inertia * body.angularVelocity
        body.ApplyAngularImpulse(angular_impulse, True)

    def _kill_lateral_velocity(
        self,
        body: b2Body,
        direction_angle: float,
        world_point: Optional[b2Vec2] = None,
        debug: bool = False
    ):
        """横滑りを抑制（タイヤは横方向に滑らない）"""
        # 適用点と速度の取得
        if world_point is None:
            world_point = body.worldCenter
            velocity = body.linearVelocity
        else:
            velocity = body.GetLinearVelocityFromWorldPoint(world_point)

        # 基準方向（前後方向）
        forward = b2Vec2(np.cos(direction_angle), np.sin(direction_angle))

        # 横方向（左右方向）
        lateral = b2Vec2(-forward.y, forward.x)

        # 横方向の速度成分
        lateral_velocity_magnitude = velocity.dot(lateral)
        lateral_velocity = lateral_velocity_magnitude * lateral

        # 横方向の速度を打ち消すインパルスを計算
        impulse = -body.mass * lateral_velocity

        # インパルスの大きさをクリップ
        impulse_length = np.linalg.norm([impulse.x, impulse.y])
        if impulse_length > self.max_lateral_impulse:
            impulse *= self.max_lateral_impulse / impulse_length

        if debug and impulse_length > 0.001:
            print(f"[DEBUG] Lateral impulse: ({impulse.x:.4f}, {impulse.y:.4f}), magnitude: {impulse_length:.4f}")

        # インパルスを適用
        body.ApplyLinearImpulse(impulse, world_point, True)
