"""車両モデル"""

from Box2D import b2World, b2Vec2, b2Body, b2PolygonShape
import numpy as np
from typing import Tuple, Dict, Optional


class Vehicle:
    """ミニカーの物理モデル"""

    # ========================================
    # 制御パラメータ定数
    # ========================================

    # ステアリング閾値
    STEERING_THRESHOLD_STRAIGHT = 0.001  # rad
    """
    ほぼ直進とみなすステアリング角度の閾値。
    この値以下の場合、トルクを発生させないために
    重心に駆動力を適用する。
    """

    STEERING_THRESHOLD_DAMPING = 0.05  # 正規化値 (-1.0 ~ 1.0)
    """
    強い角速度減衰を適用するステアリング入力の閾値。
    この値以下の場合、回転を素早く止めるために
    ANGULAR_DAMPING_STRONG を適用する。
    """

    # 角速度減衰係数
    ANGULAR_DAMPING_STRONG = 0.8
    """
    強い角速度減衰係数。
    ステアリング入力が小さい時に適用され、
    回転を素早く止める。
    """

    ANGULAR_DAMPING_NORMAL = 0.1
    """
    通常の角速度減衰係数。
    ステアリング入力がある時に適用され、
    自然な旋回を可能にする。
    """

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

        Note:
            後退時のステアリング反転は行わない（強化学習用途のため）
            Bicycle Modelの物理的な挙動に従う：
            - 前進時: 左入力 → 左回転
            - 後退時: 左入力 → 右回転（物理的に正しい挙動）
        """
        # 制御入力の正規化
        steering, throttle = self._normalize_control(steering, throttle)
        steer_angle = -steering * self.max_steering_angle

        # デバッグ情報
        if debug:
            print(f"[DEBUG] Steering: {steering:.4f}, Throttle: {throttle:.4f}")
            print(f"[DEBUG] Body angle: {self.body.angle:.4f}, Angular velocity: {self.body.angularVelocity:.4f}")

        # ホイール位置の計算
        wheel_positions = self._compute_wheel_positions()

        # 各サブシステムに制御を委譲
        self._apply_tire_friction(steer_angle, wheel_positions, debug=debug)
        self._apply_drive_force(steer_angle, throttle, wheel_positions)
        self._apply_angular_damping(steering)

    def _normalize_control(self, steering: float, throttle: float) -> Tuple[float, float]:
        """
        制御入力を正規化（-1.0 ~ 1.0にクリップ）

        Args:
            steering: ステアリング入力（生の値）
            throttle: スロットル入力（生の値）

        Returns:
            (正規化されたステアリング, 正規化されたスロットル)
        """
        steering = np.clip(steering, -1.0, 1.0)
        throttle = np.clip(throttle, -1.0, 1.0)
        return steering, throttle

    def _compute_wheel_positions(self) -> Dict:
        """
        前輪と後輪のワールド座標位置を計算

        Returns:
            {
                "front_local": b2Vec2,   # 前輪のローカル座標
                "rear_local": b2Vec2,    # 後輪のローカル座標
                "front_world": b2Vec2,   # 前輪のワールド座標
                "rear_world": b2Vec2,    # 後輪のワールド座標
                "front_angle": float,    # 前輪の角度（ワールド座標系）
                "rear_angle": float,     # 後輪の角度（ワールド座標系）
            }
        """
        # 前輪と後輪の位置（ローカル座標系）
        front_local = b2Vec2(self.wheelbase / 2, 0)  # 車体前方
        rear_local = b2Vec2(-self.wheelbase / 2, 0)  # 車体後方

        # ワールド座標系に変換
        front_world = self.body.GetWorldPoint(front_local)
        rear_world = self.body.GetWorldPoint(rear_local)

        return {
            "front_local": front_local,
            "rear_local": rear_local,
            "front_world": front_world,
            "rear_world": rear_world,
        }

    def _apply_tire_friction(self, steer_angle: float, wheel_positions: Dict, debug: bool = False):
        """
        タイヤの横滑りを抑制

        Args:
            steer_angle: ステアリング角度 (rad)
            wheel_positions: _compute_wheel_positions() の戻り値
            debug: デバッグ情報を出力するか
        """
        if abs(steer_angle) < self.STEERING_THRESHOLD_STRAIGHT:
            # 完全に真っ直ぐ進む時は、重心で横滑りを抑制（トルクなし）
            self._kill_lateral_velocity(self.body.angle, world_point=None, debug=debug)
        else:
            # ステアリングがある時は各ホイールで抑制
            front_wheel_angle = self.body.angle + steer_angle
            rear_wheel_angle = self.body.angle

            self._kill_lateral_velocity(
                front_wheel_angle,
                wheel_positions["front_world"],
                debug=debug
            )
            self._kill_lateral_velocity(
                rear_wheel_angle,
                wheel_positions["rear_world"],
                debug=debug
            )

    def _apply_drive_force(
        self,
        steer_angle: float,
        throttle: float,
        wheel_positions: Dict
    ):
        """
        駆動力を適用

        Args:
            steer_angle: ステアリング角度 (rad)
            throttle: スロットル (-1.0 ~ 1.0)
            wheel_positions: _compute_wheel_positions() の戻り値
        """
        if abs(steer_angle) < self.STEERING_THRESHOLD_STRAIGHT:
            # 真っ直ぐ進む時は車体の向きで重心に適用（トルクなし）
            direction = b2Vec2(
                np.cos(self.body.angle),
                np.sin(self.body.angle)
            )
            force = throttle * self.max_motor_force * direction
            self.body.ApplyForce(force, self.body.worldCenter, True)
        else:
            # ステアリングがある時は前輪位置に適用（通常のBicycle Model）
            front_wheel_angle = self.body.angle + steer_angle
            direction = b2Vec2(
                np.cos(front_wheel_angle),
                np.sin(front_wheel_angle)
            )
            force = throttle * self.max_motor_force * direction
            self.body.ApplyForce(force, wheel_positions["front_world"], True)

    def _apply_angular_damping(self, steering: float):
        """
        角速度の減衰を適用（回転の安定性のため）

        ステアリング入力が小さい時は強い減衰を適用し、
        回転を素早く止める。

        Args:
            steering: 正規化されたステアリング入力 (-1.0 ~ 1.0)
        """
        if abs(steering) < self.STEERING_THRESHOLD_DAMPING:
            damping = self.ANGULAR_DAMPING_STRONG
        else:
            damping = self.ANGULAR_DAMPING_NORMAL

        angular_impulse = -damping * self.body.inertia * self.body.angularVelocity
        self.body.ApplyAngularImpulse(angular_impulse, True)

    def _kill_lateral_velocity(
        self,
        direction_angle: float,
        world_point: Optional[b2Vec2] = None,
        debug: bool = False
    ):
        """
        横滑りを抑制（タイヤは横方向に滑らない）

        Args:
            direction_angle: 基準方向の角度（ワールド座標系、rad）
            world_point: インパルスを適用する位置。
                         Noneの場合は重心に適用（トルクなし）
            debug: デバッグ情報を出力するか

        Note:
            world_pointがNoneの場合、重心での速度を使用し、
            重心にインパルスを適用するため、トルクが発生しない。
        """
        # 適用点と速度の取得
        if world_point is None:
            # 重心での処理（トルクなし）
            world_point = self.body.worldCenter
            velocity = self.body.linearVelocity
        else:
            # 指定位置での処理
            velocity = self.body.GetLinearVelocityFromWorldPoint(world_point)

        # 基準方向（前後方向）
        forward = b2Vec2(np.cos(direction_angle), np.sin(direction_angle))

        # 横方向（左右方向）
        lateral = b2Vec2(-forward.y, forward.x)

        # 横方向の速度成分
        lateral_velocity_magnitude = velocity.dot(lateral)

        # 横方向の速度ベクトル
        lateral_velocity = lateral_velocity_magnitude * lateral

        # 横方向の速度を打ち消すインパルスを計算
        impulse = -self.body.mass * lateral_velocity

        # インパルスの大きさをクリップ（安定性のため重要）
        impulse_length = np.linalg.norm([impulse.x, impulse.y])
        if impulse_length > self.max_lateral_impulse:
            impulse *= self.max_lateral_impulse / impulse_length

        if debug and impulse_length > 0.001:
            print(f"[DEBUG] Lateral impulse: ({impulse.x:.4f}, {impulse.y:.4f}), magnitude: {impulse_length:.4f}")

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
