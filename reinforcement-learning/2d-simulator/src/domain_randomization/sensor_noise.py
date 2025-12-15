"""センサーノイズの統合

既存のLiDARSensor.add_advanced_noise()を活用し、
エピソードごとにノイズレベルをランダム化する。
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class SensorNoiseConfig:
    """センサーノイズの設定

    各パラメータは (min, max) のタプルで範囲を指定。
    Noneの場合はノイズを無効化。
    """

    # ガウシアンノイズレベルの範囲（距離に対する割合）
    noise_level_range: Optional[tuple] = (0.01, 0.02)

    # ドロップアウト確率の範囲
    dropout_prob_range: Optional[tuple] = (0.02, 0.05)

    # スパイクノイズ確率の範囲
    spike_prob_range: Optional[tuple] = (0.005, 0.01)

    # 乱数シード（再現性のため、Noneで毎回変わる）
    seed: Optional[int] = None


class SensorNoiseRandomizer:
    """センサーノイズのランダム化を管理するクラス

    エピソードごとに呼び出され、ノイズパラメータをランダム化。

    Example:
        >>> config = SensorNoiseConfig()
        >>> randomizer = SensorNoiseRandomizer(config)
        >>> noise_params = randomizer.get_noise_params()
        >>> # LiDARSensor.add_advanced_noise()に渡す
    """

    def __init__(self, config: SensorNoiseConfig):
        """
        Args:
            config: ノイズ設定
        """
        self.config = config
        self._rng = np.random.default_rng(config.seed)

    def get_noise_params(self) -> dict:
        """ノイズパラメータをランダム化

        Returns:
            LiDARSensor.add_advanced_noise()に渡すパラメータ
            {
                'noise_level': 0.015,
                'dropout_prob': 0.03,
                'spike_prob': 0.008,
            }
        """
        params = {}

        # ガウシアンノイズレベル
        if self.config.noise_level_range is not None:
            params['noise_level'] = self._rng.uniform(*self.config.noise_level_range)
        else:
            params['noise_level'] = 0.0

        # ドロップアウト確率
        if self.config.dropout_prob_range is not None:
            params['dropout_prob'] = self._rng.uniform(*self.config.dropout_prob_range)
        else:
            params['dropout_prob'] = 0.0

        # スパイクノイズ確率
        if self.config.spike_prob_range is not None:
            params['spike_prob'] = self._rng.uniform(*self.config.spike_prob_range)
        else:
            params['spike_prob'] = 0.0

        return params

    def apply_noise(self, lidar_sensor, distances: np.ndarray) -> np.ndarray:
        """LiDARスキャンにノイズを適用

        Args:
            lidar_sensor: LiDARSensorインスタンス
            distances: クリーンな距離データ

        Returns:
            ノイズを加えた距離データ
        """
        params = self.get_noise_params()

        # ノイズレベルがすべて0の場合はそのまま返す
        if (params['noise_level'] == 0.0 and
            params['dropout_prob'] == 0.0 and
            params['spike_prob'] == 0.0):
            return distances

        # 既存のadd_advanced_noise()メソッドを使用
        return lidar_sensor.add_advanced_noise(
            distances,
            noise_level=params['noise_level'],
            dropout_prob=params['dropout_prob'],
            spike_prob=params['spike_prob'],
        )


# デフォルト設定のインスタンス
DEFAULT_SENSOR_NOISE_CONFIG = SensorNoiseConfig()

# 軽微なノイズ設定（最初のテスト用）
MILD_SENSOR_NOISE_CONFIG = SensorNoiseConfig(
    noise_level_range=(0.005, 0.01),
    dropout_prob_range=(0.01, 0.02),
    spike_prob_range=(0.002, 0.005),
)

# 強めのノイズ設定（実機転移用）
STRONG_SENSOR_NOISE_CONFIG = SensorNoiseConfig(
    noise_level_range=(0.01, 0.02),
    dropout_prob_range=(0.02, 0.05),
    spike_prob_range=(0.005, 0.01),
)
