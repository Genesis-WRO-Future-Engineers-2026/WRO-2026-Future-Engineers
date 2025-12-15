"""車両モデル（リファクタリング版）"""

from Box2D import b2World, b2Vec2, b2Body
import numpy as np
from typing import Tuple, Dict, Optional

# リファクタリング後のモジュール
from src.env.vehicle.config import VehicleConfig
from src.env.vehicle.physics_params import PhysicsParameters
from src.env.vehicle.bicycle_model import BicycleModelController


class Vehicle:
    """ミニカーの物理モデル（リファクタリング版）

    責務を以下のコンポーネントに委譲:
    - VehicleConfig: 車両寸法・制御パラメータ
    - PhysicsParameters: Domain Randomization用パラメータ
    - BicycleModelController: Bicycle Model物理計算
    """

    def __init__(
        self,
        world: b2World,
        start_pos: Tuple[float, float],
        start_angle: float = 0.0,
        # 後方互換性のためのパラメータ（非推奨）
        mass: float = 1.4,
        friction: float = 0.7,
        linear_damping: float = 0.5,
        angular_damping: float = 0.8,
        max_motor_force: float = 20.0,
        max_lateral_impulse: float = 2.5,
        # リファクタリング後の依存性注入
        config: Optional[VehicleConfig] = None,
        physics_params: Optional[PhysicsParameters] = None,
        bicycle_controller: Optional[BicycleModelController] = None,
    ):
        """
        Args:
            world: Box2Dの物理世界
            start_pos: 初期位置 (x, y)
            start_angle: 初期角度 (rad)
            mass: 質量（後方互換性用、非推奨）
            friction: 摩擦係数（後方互換性用、非推奨）
            linear_damping: 線形減衰（後方互換性用、非推奨）
            angular_damping: 角減衰（後方互換性用、非推奨）
            max_motor_force: 最大モーター力（後方互換性用、非推奨）
            max_lateral_impulse: 最大横滑りインパルス（後方互換性用、非推奨）
            config: 車両設定（Noneの場合はデフォルト作成）
            physics_params: 物理パラメータ（Noneの場合はデフォルト作成）
            bicycle_controller: Bicycle Modelコントローラー（Noneの場合は作成）
        """
        self.world = world

        # 設定の注入または作成
        self.config = config if config is not None else VehicleConfig.create_default()

        # 物理パラメータの注入または作成（後方互換性のため、引数を優先）
        if physics_params is not None:
            self.physics_params = physics_params
        else:
            self.physics_params = PhysicsParameters(
                mass=mass,
                friction=friction,
                linear_damping=linear_damping,
                angular_damping=angular_damping,
                max_motor_force=max_motor_force,
                max_lateral_impulse=max_lateral_impulse,
            )

        # Bicycle Modelコントローラーの注入または作成
        if bicycle_controller is not None:
            self.controller = bicycle_controller
        else:
            self.controller = BicycleModelController(
                config=self.config,
                max_motor_force=self.physics_params.max_motor_force,
                max_lateral_impulse=self.physics_params.max_lateral_impulse,
            )

        # Box2Dボディ作成
        self.body = self._create_body(start_pos, start_angle)

        # 後方互換性のため、古いプロパティを保持
        self.width = self.config.width
        self.length = self.config.length
        self.mass = self.physics_params.mass
        self.wheelbase = self.config.wheelbase
        self.max_steering_angle = self.config.max_steering_angle
        self.max_motor_force = self.physics_params.max_motor_force
        self.max_lateral_impulse = self.physics_params.max_lateral_impulse

    def _create_body(self, start_pos: Tuple[float, float], start_angle: float) -> b2Body:
        """Box2Dボディを作成"""
        body = self.world.CreateDynamicBody(
            position=b2Vec2(*start_pos),
            angle=start_angle,
            linearDamping=self.physics_params.linear_damping,
            angularDamping=self.physics_params.angular_damping,
        )

        # 車両の識別子を設定（衝突検出用）
        body.userData = "vehicle"

        # 車両の形状（矩形）
        body.CreatePolygonFixture(
            box=(self.config.length / 2, self.config.width / 2),
            density=self.physics_params.mass / (self.config.length * self.config.width),
            friction=self.physics_params.friction,
        )

        return body

    def apply_control(self, steering: float, throttle: float, debug: bool = False):
        """制御入力を適用（BicycleModelControllerに委譲）

        Args:
            steering: ステアリング角度 (-1.0 ~ 1.0)
            throttle: スロットル (-1.0 ~ 1.0) 負の値で後退
            debug: デバッグ情報を出力するか
        """
        # 制御入力の正規化
        steering = np.clip(steering, -1.0, 1.0)
        throttle = np.clip(throttle, -1.0, 1.0)

        # Bicycle Modelコントローラーに委譲
        self.controller.apply_control(self.body, steering, throttle, debug=debug)

    def get_state(self) -> Dict:
        """現在の状態を取得"""
        return {
            "position": (self.body.position.x, self.body.position.y),
            "angle": self.body.angle,
            "velocity": (self.body.linearVelocity.x, self.body.linearVelocity.y),
            "angular_velocity": self.body.angularVelocity,
            "speed": np.linalg.norm(
                [self.body.linearVelocity.x, self.body.linearVelocity.y]
            ),
        }

    def reset(
        self,
        position: Tuple[float, float],
        angle: float = 0.0,
        # 後方互換性のためのパラメータ（非推奨）
        mass: Optional[float] = None,
        friction: Optional[float] = None,
        linear_damping: Optional[float] = None,
        angular_damping: Optional[float] = None,
        max_motor_force: Optional[float] = None,
        max_lateral_impulse: Optional[float] = None,
        # リファクタリング後のパラメータ
        physics_params: Optional[PhysicsParameters] = None,
    ):
        """車両を初期状態にリセット

        Args:
            position: リセット位置 (x, y)
            angle: リセット角度 (rad)
            mass: 質量（後方互換性用、非推奨）
            friction: 摩擦係数（後方互換性用、非推奨）
            linear_damping: 線形減衰（後方互換性用、非推奨）
            angular_damping: 角減衰（後方互換性用、非推奨）
            max_motor_force: 最大モーター力（後方互換性用、非推奨）
            max_lateral_impulse: 最大横滑りインパルス（後方互換性用、非推奨）
            physics_params: 物理パラメータ（推奨）
        """
        # 後方互換性のため、個別パラメータからPhysicsParametersを作成
        if physics_params is None and any([
            mass is not None,
            friction is not None,
            linear_damping is not None,
            angular_damping is not None,
            max_motor_force is not None,
            max_lateral_impulse is not None,
        ]):
            physics_params = PhysicsParameters(
                mass=mass,
                friction=friction,
                linear_damping=linear_damping,
                angular_damping=angular_damping,
                max_motor_force=max_motor_force,
                max_lateral_impulse=max_lateral_impulse,
            )

        # 物理パラメータを更新（指定された場合のみ）
        if physics_params is not None and physics_params.has_updates():
            self._update_physics_params(physics_params)

        # 位置と速度をリセット
        self.body.position = b2Vec2(*position)
        self.body.angle = angle
        self.body.linearVelocity = b2Vec2(0, 0)
        self.body.angularVelocity = 0

    def _update_physics_params(self, params: PhysicsParameters):
        """物理パラメータを更新"""
        # 質量の更新
        if params.mass is not None:
            self.physics_params.mass = params.mass
            self.mass = params.mass  # 後方互換性
            for fixture in self.body.fixtures:
                fixture.density = self.physics_params.mass / (self.config.length * self.config.width)
            self.body.ResetMassData()

        # ボディパラメータの更新
        if params.linear_damping is not None:
            self.physics_params.linear_damping = params.linear_damping
            self.body.linearDamping = params.linear_damping

        if params.angular_damping is not None:
            self.physics_params.angular_damping = params.angular_damping
            self.body.angularDamping = params.angular_damping

        # フィクスチャの摩擦係数を更新
        if params.friction is not None:
            self.physics_params.friction = params.friction
            for fixture in self.body.fixtures:
                fixture.friction = params.friction

        # コントローラーのパラメータを更新
        if params.max_motor_force is not None:
            self.physics_params.max_motor_force = params.max_motor_force
            self.max_motor_force = params.max_motor_force  # 後方互換性
            self.controller.max_motor_force = params.max_motor_force

        if params.max_lateral_impulse is not None:
            self.physics_params.max_lateral_impulse = params.max_lateral_impulse
            self.max_lateral_impulse = params.max_lateral_impulse  # 後方互換性
            self.controller.max_lateral_impulse = params.max_lateral_impulse
