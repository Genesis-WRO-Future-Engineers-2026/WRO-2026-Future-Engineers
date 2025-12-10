"""車両モデル"""

from Box2D import b2World, b2Vec2, b2Body, b2PolygonShape
import numpy as np
from typing import Tuple, Dict


class Vehicle:
    """ミニカーの物理モデル"""

    def __init__(
        self,
        world: b2World,
        start_pos: Tuple[float, float],
        start_angle: float = 0.0,
    ):
        """
        Args:
            world: Box2Dの物理世界
            start_pos: 初期位置 (x, y)
            start_angle: 初期角度 (rad)
        """
        self.world = world

        # 車両パラメータ
        self.width = 0.2  # m
        self.length = 0.4  # m
        self.mass = 1.0  # kg
        self.wheelbase = 0.28  # m (前輪と後輪の距離)

        self.max_steering_angle = 0.5  # rad (約28度)
        self.max_motor_force = 20.0  # N
        self.max_lateral_impulse = 2.5  # 横滑り抑制の最大インパルス（安定性のため）

        # Box2Dボディ作成
        self.body = self.world.CreateDynamicBody(
            position=b2Vec2(*start_pos),
            angle=start_angle,
            linearDamping=0.5,  # 空気抵抗
            angularDamping=0.8,  # 回転抵抗
        )

        # 車両の形状（矩形）
        self.body.CreatePolygonFixture(
            box=(self.length / 2, self.width / 2),
            density=self.mass / (self.length * self.width),
            friction=0.7,
        )

    def apply_control(self, steering: float, throttle: float, debug: bool = False):
        """
        制御入力を適用（Bicycle Modelベース）

        Args:
            steering: ステアリング角度 (-1.0 ~ 1.0)
            throttle: スロットル (-1.0 ~ 1.0) 負の値で後退
            debug: デバッグ情報を出力するか
        """
        # パラメータのクリッピング
        steering = np.clip(steering, -1.0, 1.0)
        throttle = np.clip(throttle, -1.0, 1.0)
        steer_angle = steering * self.max_steering_angle

        # 後退時のステアリング反転は行わない（強化学習用途のため）
        # Bicycle Modelの物理的な挙動に従う：
        # - 前進時: 左入力 → 左回転
        # - 後退時: 左入力 → 右回転（物理的に正しい挙動）

        # 前輪と後輪の位置（ローカル座標系）
        front_wheel_local = b2Vec2(self.wheelbase / 2, 0)  # 車体前方
        rear_wheel_local = b2Vec2(-self.wheelbase / 2, 0)  # 車体後方

        # ワールド座標系に変換
        front_wheel_world = self.body.GetWorldPoint(front_wheel_local)
        rear_wheel_world = self.body.GetWorldPoint(rear_wheel_local)

        # 各ホイールの向き（ワールド座標系）
        front_wheel_angle = self.body.angle + steer_angle  # 前輪：ステアリング角度分回転
        rear_wheel_angle = self.body.angle  # 後輪：車体と同じ向き

        # デバッグ情報
        if debug:
            print(f"[DEBUG] Steering: {steering:.4f}, Throttle: {throttle:.4f}")
            print(f"[DEBUG] Body angle: {self.body.angle:.4f}, Angular velocity: {self.body.angularVelocity:.4f}")
            front_vel = self.body.GetLinearVelocityFromWorldPoint(front_wheel_world)
            rear_vel = self.body.GetLinearVelocityFromWorldPoint(rear_wheel_world)
            print(f"[DEBUG] Front wheel velocity: ({front_vel.x:.4f}, {front_vel.y:.4f})")
            print(f"[DEBUG] Rear wheel velocity: ({rear_vel.x:.4f}, {rear_vel.y:.4f})")

        # 各ホイール位置で横滑りを抑制
        # ステアリングが非常に小さい時は、重心での横滑りのみを抑制してトルクを防ぐ
        if abs(steer_angle) < 0.001:
            # 完全に真っ直ぐ進む時は、重心で横滑りを抑制（トルクなし）
            self._kill_lateral_velocity_at_center(self.body.angle, debug=debug)
        else:
            # ステアリングがある時は通常通り
            self._kill_lateral_velocity(front_wheel_world, front_wheel_angle, debug=debug)
            self._kill_lateral_velocity(rear_wheel_world, rear_wheel_angle, debug=debug)

        # 駆動力を適用
        # ステアリングが小さい時は重心に適用してトルクを防ぐ
        if abs(steer_angle) < 0.001:
            # 真っ直ぐ進む時は車体の向きで重心に適用
            drive_direction = b2Vec2(np.cos(self.body.angle), np.sin(self.body.angle))
            force = throttle * self.max_motor_force * drive_direction
            self.body.ApplyForce(force, self.body.worldCenter, True)
        else:
            # ステアリングがある時は前輪位置に適用（通常のBicycle Model）
            front_direction = b2Vec2(
                np.cos(front_wheel_angle), np.sin(front_wheel_angle)
            )
            force = throttle * self.max_motor_force * front_direction
            self.body.ApplyForce(force, front_wheel_world, True)

        # 角速度の減衰（回転の安定性のため）
        # ステアリング入力が小さい時は、角速度をより強く減衰させる
        if abs(steering) < 0.05:  # ステアリング入力が小さい時（-0.05 ~ +0.05）
            # 強い減衰を適用して回転を素早く止める
            angular_damping = 0.8
        else:
            # 通常の減衰
            angular_damping = 0.1
        angular_impulse = -angular_damping * self.body.inertia * self.body.angularVelocity
        self.body.ApplyAngularImpulse(angular_impulse, True)

    def _kill_lateral_velocity_at_center(self, vehicle_angle: float, debug: bool = False):
        """
        車体重心での横滑りを抑制（トルクを発生させない）

        Args:
            vehicle_angle: 車体の向き（ワールド座標系での角度）
            debug: デバッグ情報を出力するか
        """
        # 重心での速度を取得
        center_velocity = self.body.linearVelocity

        # 車体の向き（前後方向）
        vehicle_forward = b2Vec2(np.cos(vehicle_angle), np.sin(vehicle_angle))

        # 車体の横方向（左右方向）
        vehicle_lateral = b2Vec2(-vehicle_forward.y, vehicle_forward.x)

        # 横方向の速度成分
        lateral_velocity_magnitude = center_velocity.dot(vehicle_lateral)

        # 横方向の速度ベクトル
        lateral_velocity = lateral_velocity_magnitude * vehicle_lateral

        # 横方向の速度を打ち消すインパルスを計算
        impulse = -self.body.mass * lateral_velocity

        # インパルスの大きさをクリップ
        impulse_length = np.linalg.norm([impulse.x, impulse.y])
        if impulse_length > self.max_lateral_impulse:
            impulse *= self.max_lateral_impulse / impulse_length

        if debug and impulse_length > 0.001:
            print(f"[DEBUG] Center lateral impulse: ({impulse.x:.4f}, {impulse.y:.4f}), magnitude: {impulse_length:.4f}")

        # インパルスを重心に適用（トルクなし）
        self.body.ApplyLinearImpulse(impulse, self.body.worldCenter, True)

    def _kill_lateral_velocity(self, world_point: b2Vec2, wheel_angle: float, debug: bool = False):
        """
        ホイール位置での横滑りを抑制（タイヤは横方向に滑らない）

        Args:
            world_point: ホイールのワールド座標位置
            wheel_angle: ホイールの向き（ワールド座標系での角度）
            debug: デバッグ情報を出力するか
        """
        # ホイール位置での速度を取得
        point_velocity = self.body.GetLinearVelocityFromWorldPoint(world_point)

        # ホイールの向き（前後方向）
        wheel_forward = b2Vec2(np.cos(wheel_angle), np.sin(wheel_angle))

        # ホイールの横方向（左右方向）
        wheel_lateral = b2Vec2(-wheel_forward.y, wheel_forward.x)

        # 横方向の速度成分
        lateral_velocity_magnitude = point_velocity.dot(wheel_lateral)

        # 横方向の速度ベクトル
        lateral_velocity = lateral_velocity_magnitude * wheel_lateral

        # 横方向の速度を打ち消すインパルスを計算
        impulse = -self.body.mass * lateral_velocity

        # インパルスの大きさをクリップ（安定性のため重要）
        impulse_length = np.linalg.norm([impulse.x, impulse.y])
        if impulse_length > self.max_lateral_impulse:
            impulse *= self.max_lateral_impulse / impulse_length

        if debug and impulse_length > 0.001:
            print(f"[DEBUG]   Lateral impulse: ({impulse.x:.4f}, {impulse.y:.4f}), magnitude: {impulse_length:.4f}")

        # インパルスを適用
        self.body.ApplyLinearImpulse(impulse, world_point, True)

    def get_state(self) -> Dict:
        """
        現在の状態を取得

        Returns:
            状態の辞書
        """
        return {
            "position": (self.body.position.x, self.body.position.y),
            "angle": self.body.angle,
            "velocity": (self.body.linearVelocity.x, self.body.linearVelocity.y),
            "angular_velocity": self.body.angularVelocity,
            "speed": np.linalg.norm(
                [self.body.linearVelocity.x, self.body.linearVelocity.y]
            ),
        }

    def reset(self, position: Tuple[float, float], angle: float = 0.0):
        """
        車両を初期状態にリセット

        Args:
            position: リセット位置 (x, y)
            angle: リセット角度 (rad)
        """
        self.body.position = b2Vec2(*position)
        self.body.angle = angle
        self.body.linearVelocity = b2Vec2(0, 0)
        self.body.angularVelocity = 0
