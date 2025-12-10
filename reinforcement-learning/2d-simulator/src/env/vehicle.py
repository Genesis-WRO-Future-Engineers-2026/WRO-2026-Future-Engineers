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

    def apply_control(self, steering: float, throttle: float):
        """
        制御入力を適用（Bicycle Modelベース）

        Args:
            steering: ステアリング角度 (-1.0 ~ 1.0)
            throttle: スロットル (-1.0 ~ 1.0) 負の値で後退
        """
        # パラメータのクリッピング
        steering = np.clip(steering, -1.0, 1.0)
        throttle = np.clip(throttle, -1.0, 1.0)
        steer_angle = steering * self.max_steering_angle

        # 前輪と後輪の位置（ローカル座標系）
        front_wheel_local = b2Vec2(self.wheelbase / 2, 0)  # 車体前方
        rear_wheel_local = b2Vec2(-self.wheelbase / 2, 0)  # 車体後方

        # ワールド座標系に変換
        front_wheel_world = self.body.GetWorldPoint(front_wheel_local)
        rear_wheel_world = self.body.GetWorldPoint(rear_wheel_local)

        # 各ホイールの向き（ワールド座標系）
        front_wheel_angle = self.body.angle + steer_angle  # 前輪：ステアリング角度分回転
        rear_wheel_angle = self.body.angle  # 後輪：車体と同じ向き

        # 各ホイール位置で横滑りを抑制
        self._kill_lateral_velocity(front_wheel_world, front_wheel_angle)
        self._kill_lateral_velocity(rear_wheel_world, rear_wheel_angle)

        # 駆動力を前輪の向きに沿って適用
        front_direction = b2Vec2(
            np.cos(front_wheel_angle), np.sin(front_wheel_angle)
        )
        force = throttle * self.max_motor_force * front_direction
        self.body.ApplyForce(force, front_wheel_world, True)

        # 角速度の減衰（回転の安定性のため）
        angular_impulse = -0.1 * self.body.inertia * self.body.angularVelocity
        self.body.ApplyAngularImpulse(angular_impulse, True)

    def _kill_lateral_velocity(self, world_point: b2Vec2, wheel_angle: float):
        """
        ホイール位置での横滑りを抑制（タイヤは横方向に滑らない）

        Args:
            world_point: ホイールのワールド座標位置
            wheel_angle: ホイールの向き（ワールド座標系での角度）
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
