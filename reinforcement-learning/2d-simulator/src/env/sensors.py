"""センサーシミュレーション"""

from Box2D import b2World, b2Vec2, b2RayCastCallback
import numpy as np
from typing import Tuple, Optional


class RayCastClosestCallback(b2RayCastCallback):
    """最も近い衝突点を見つけるレイキャストコールバック"""

    def __init__(self):
        super().__init__()
        self.hit = False
        self.point = None
        self.normal = None
        self.fraction = 1.0

    def ReportFixture(self, fixture, point, normal, fraction):
        """
        レイキャストの衝突時に呼ばれる

        Args:
            fixture: 衝突したフィクスチャ
            point: 衝突点
            normal: 法線ベクトル
            fraction: レイ上の位置（0-1）

        Returns:
            fraction: 次の探索範囲
        """
        self.hit = True
        self.point = b2Vec2(point)
        self.normal = b2Vec2(normal)
        self.fraction = fraction
        return fraction  # 最も近い点を探すため


class LiDARSensor:
    """2D LiDARセンサーのシミュレーション"""

    def __init__(
        self,
        world: b2World,
        num_rays: int = 72,
        max_range: float = 10.0,
        angle_min: float = 0.0,
        angle_max: float = 2 * np.pi,
    ):
        """
        Args:
            world: Box2Dの物理世界
            num_rays: レイの本数（デフォルト: 72本 = 5度刻み）
            max_range: 最大測定距離 (m)
            angle_min: 最小角度 (rad)
            angle_max: 最大角度 (rad)
        """
        self.world = world
        self.num_rays = num_rays
        self.max_range = max_range
        self.angle_min = angle_min
        self.angle_max = angle_max

        # 各レイの角度
        self.angles = np.linspace(angle_min, angle_max, num_rays, endpoint=False)

    def scan(
        self, position: Tuple[float, float], orientation: float
    ) -> np.ndarray:
        """
        LiDARスキャンを実行

        Args:
            position: センサー位置 (x, y)
            orientation: センサーの向き (rad)

        Returns:
            distances: 各方向の距離 (num_rays,)
        """
        distances = np.zeros(self.num_rays)
        start_point = b2Vec2(*position)

        for i, angle in enumerate(self.angles):
            # 絶対角度
            absolute_angle = orientation + angle

            # レイの終点
            direction = b2Vec2(np.cos(absolute_angle), np.sin(absolute_angle))
            end_point = start_point + self.max_range * direction

            # レイキャスト
            callback = RayCastClosestCallback()
            self.world.RayCast(callback, start_point, end_point)

            if callback.hit:
                # 衝突点までの距離
                hit_distance = self.max_range * callback.fraction
                distances[i] = hit_distance
            else:
                # 衝突なし
                distances[i] = self.max_range

        return distances

    def add_noise(
        self, distances: np.ndarray, noise_level: float = 0.01
    ) -> np.ndarray:
        """
        ガウシアンノイズを追加

        Args:
            distances: 距離データ
            noise_level: ノイズレベル（最大距離に対する割合）

        Returns:
            ノイズ付き距離データ
        """
        noise = np.random.normal(0, noise_level * self.max_range, distances.shape)
        noisy_distances = distances + noise
        return np.clip(noisy_distances, 0, self.max_range)

    def add_advanced_noise(
        self,
        distances: np.ndarray,
        noise_level: float = 0.01,
        dropout_prob: float = 0.05,
        spike_prob: float = 0.01,
    ) -> np.ndarray:
        """
        高度なノイズモデル（ガウシアン + ドロップアウト + スパイク）

        Args:
            distances: 距離データ
            noise_level: ガウシアンノイズレベル
            dropout_prob: ドロップアウト確率（レイが無効になる）
            spike_prob: スパイクノイズ確率（外れ値）

        Returns:
            ノイズ付き距離データ
        """
        # ガウシアンノイズ
        noise = np.random.normal(0, noise_level * self.max_range, distances.shape)
        noisy_distances = distances + noise

        # ドロップアウト（一部のレイが無効）
        dropout_mask = np.random.random(distances.shape) > dropout_prob
        noisy_distances = np.where(dropout_mask, noisy_distances, self.max_range)

        # スパイクノイズ（外れ値）
        spike_mask = np.random.random(distances.shape) < spike_prob
        spike_values = np.random.uniform(0, self.max_range, distances.shape)
        noisy_distances = np.where(spike_mask, spike_values, noisy_distances)

        return np.clip(noisy_distances, 0, self.max_range)
