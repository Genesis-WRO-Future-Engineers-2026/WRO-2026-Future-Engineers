"""車両の設定管理"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ControlParameters:
    """制御パラメータ

    Bicycle Modelの制御ロジックで使用する閾値と減衰係数。
    """

    # ステアリング閾値
    steering_threshold_straight: float = 0.001  # rad
    steering_threshold_damping: float = 0.05    # 正規化値

    # 角速度減衰係数
    angular_damping_strong: float = 0.8
    angular_damping_normal: float = 0.1


@dataclass
class VehicleConfig:
    """車両の設定

    実機TT-02に合わせた寸法と制御パラメータ。
    """

    # 車両の物理的寸法（実機TT-02）
    width: float = 0.188        # m (実機: 188mm)
    length: float = 0.479       # m (実機: 479mm)
    wheelbase: float = 0.257    # m (実機: 257mm、標準設定)

    # 制御パラメータ
    max_steering_angle: float = 0.5  # rad (約28度)

    # 制御ロジックの詳細パラメータ
    control_params: ControlParameters = field(default_factory=ControlParameters)

    @classmethod
    def create_default(cls) -> 'VehicleConfig':
        """デフォルト設定を作成"""
        return cls()

    @classmethod
    def create_custom(
        cls,
        width: float = 0.188,
        length: float = 0.479,
        wheelbase: float = 0.257,
        max_steering_angle: float = 0.5,
        **control_params_kwargs
    ) -> 'VehicleConfig':
        """カスタム設定を作成

        Args:
            width: 車両の幅
            length: 車両の長さ
            wheelbase: ホイールベース
            max_steering_angle: 最大ステアリング角度
            **control_params_kwargs: ControlParametersに渡す引数
        """
        control_params = ControlParameters(**control_params_kwargs)
        return cls(
            width=width,
            length=length,
            wheelbase=wheelbase,
            max_steering_angle=max_steering_angle,
            control_params=control_params,
        )

    def to_dict(self) -> Dict:
        """設定を辞書に変換（保存用）"""
        return {
            'width': self.width,
            'length': self.length,
            'wheelbase': self.wheelbase,
            'max_steering_angle': self.max_steering_angle,
            'control_params': {
                'steering_threshold_straight': self.control_params.steering_threshold_straight,
                'steering_threshold_damping': self.control_params.steering_threshold_damping,
                'angular_damping_strong': self.control_params.angular_damping_strong,
                'angular_damping_normal': self.control_params.angular_damping_normal,
            }
        }
