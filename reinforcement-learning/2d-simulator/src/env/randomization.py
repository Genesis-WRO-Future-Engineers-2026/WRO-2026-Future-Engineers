"""Domain Randomization管理"""

from typing import Optional, Dict
from src.domain_randomization.physics_randomizer import (
    PhysicsRandomizer,
    PhysicsRandomizationConfig,
    DEFAULT_PHYSICS_CONFIG,
)
from src.domain_randomization.sensor_noise import (
    SensorNoiseRandomizer,
    SensorNoiseConfig,
    DEFAULT_SENSOR_NOISE_CONFIG,
)


class RandomizationManager:
    """Domain Randomizationの管理を担当するクラス

    物理パラメータのランダム化とセンサーノイズの適用を管理する。
    """

    def __init__(
        self,
        enabled: bool = False,
        physics_config: Optional[PhysicsRandomizationConfig] = None,
        sensor_noise_config: Optional[SensorNoiseConfig] = None,
    ):
        """
        Args:
            enabled: Domain Randomizationを有効化
            physics_config: 物理ランダム化の設定（Noneの場合はデフォルト）
            sensor_noise_config: センサーノイズの設定（Noneの場合はデフォルト）
        """
        self.enabled = enabled

        if self.enabled:
            # 物理ランダム化
            self.physics_randomizer = PhysicsRandomizer(
                physics_config if physics_config is not None else DEFAULT_PHYSICS_CONFIG
            )

            # センサーノイズ
            self.sensor_noise_randomizer = SensorNoiseRandomizer(
                sensor_noise_config if sensor_noise_config is not None else DEFAULT_SENSOR_NOISE_CONFIG
            )

            print("[INFO] Domain Randomization enabled")
        else:
            self.physics_randomizer = None
            self.sensor_noise_randomizer = None

    def randomize_physics(self) -> Dict:
        """物理パラメータをランダム化

        Returns:
            ランダム化された物理パラメータの辞書
            Domain Randomizationが無効な場合は空辞書
        """
        if self.enabled and self.physics_randomizer is not None:
            return self.physics_randomizer.randomize()
        return {}

    def get_sensor_noise_randomizer(self):
        """センサーノイズランダマイザーを取得

        Returns:
            SensorNoiseRandomizer（無効な場合はNone）
        """
        if self.enabled:
            return self.sensor_noise_randomizer
        return None
