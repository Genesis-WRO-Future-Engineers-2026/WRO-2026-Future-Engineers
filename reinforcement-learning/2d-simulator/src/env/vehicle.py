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

        self.max_steering_angle = 0.5  # rad (約28度)
        self.max_motor_force = 20.0  # N

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
        制御入力を適用

        Args:
            steering: ステアリング角度 (-1.0 ~ 1.0)
            throttle: スロットル (-1.0 ~ 1.0) 負の値で後退
        """
        # ステアリング角度
        steer_angle = np.clip(steering, -1.0, 1.0) * self.max_steering_angle

        # 車両の向き
        angle = self.body.angle
        direction = b2Vec2(
            np.cos(angle + steer_angle), np.sin(angle + steer_angle)
        )

        # モーター力を適用（負の値で後退）
        throttle = np.clip(throttle, -1.0, 1.0)
        force = throttle * self.max_motor_force * direction
        self.body.ApplyForceToCenter(force, True)

        # 横滑り抑制
        self._apply_lateral_friction()

    def _apply_lateral_friction(self):
        """横方向の速度を抑制（簡易的なタイヤモデル）"""
        velocity = self.body.linearVelocity
        angle = self.body.angle

        # 車両座標系での速度成分
        forward = b2Vec2(np.cos(angle), np.sin(angle))
        lateral = b2Vec2(-np.sin(angle), np.cos(angle))

        # 横方向の速度
        lateral_vel = velocity.dot(lateral)

        # 横方向の速度を減衰（タイヤのグリップを模擬）
        impulse = -lateral_vel * self.mass * 0.5 * lateral
        self.body.ApplyLinearImpulse(impulse, self.body.position, True)

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
