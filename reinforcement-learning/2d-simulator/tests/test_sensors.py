"""センサーのテスト"""

import pytest
import numpy as np
from src.physics.box2d_wrapper import PhysicsWorld
from src.env.sensors import LiDARSensor


def test_lidar_creation():
    """LiDARセンサーが正しく作成されるか"""
    world = PhysicsWorld()
    lidar = LiDARSensor(world.world)

    assert lidar is not None
    assert lidar.num_rays == 72
    assert lidar.max_range == 10.0


def test_lidar_scan_no_obstacles():
    """障害物がない場合のスキャン"""
    world = PhysicsWorld()
    lidar = LiDARSensor(world.world, num_rays=36)

    distances = lidar.scan(position=(0, 0), orientation=0)

    assert len(distances) == 36
    # 障害物がないのでmax_range
    assert np.all(distances == lidar.max_range)


def test_lidar_scan_with_wall():
    """壁がある場合のスキャン"""
    world = PhysicsWorld()

    # 右側に壁を配置（x=5の位置）
    world.add_wall_segment((5, -10), (5, 10))

    lidar = LiDARSensor(world.world, num_rays=72)

    # 原点からスキャン（正面は+x方向）
    distances = lidar.scan(position=(0, 0), orientation=0)

    assert len(distances) == 72

    # 正面方向（0度）は壁まで約5m
    assert 4.5 < distances[0] < 5.5

    # 後方（180度）は壁がないのでmax_range
    assert distances[36] == lidar.max_range


def test_lidar_scan_with_box():
    """箱型の障害物がある場合"""
    world = PhysicsWorld()

    # 前方に箱を配置
    world.add_static_box(center=(3, 0), width=1, height=1)

    lidar = LiDARSensor(world.world, num_rays=72)
    distances = lidar.scan(position=(0, 0), orientation=0)

    # 正面方向に箱があるので、距離は約2.5m（箱の端まで）
    assert distances[0] < 5.0
    assert distances[0] > 2.0


def test_lidar_different_orientations():
    """異なる方向からのスキャン"""
    world = PhysicsWorld()

    # 右側に壁
    world.add_wall_segment((5, -10), (5, 10))

    lidar = LiDARSensor(world.world, num_rays=72)

    # 正面（0度）
    distances_0 = lidar.scan(position=(0, 0), orientation=0)

    # 90度回転
    distances_90 = lidar.scan(position=(0, 0), orientation=np.pi / 2)

    # 値が異なることを確認
    assert not np.allclose(distances_0, distances_90)


def test_lidar_noise():
    """ガウシアンノイズの追加"""
    world = PhysicsWorld()
    lidar = LiDARSensor(world.world)

    # クリーンなスキャン
    clean_scan = np.ones(72) * 5.0

    # ノイズ追加
    noisy_scan = lidar.add_noise(clean_scan, noise_level=0.1)

    # ノイズが追加されている
    assert not np.allclose(clean_scan, noisy_scan)

    # 範囲内に収まっている
    assert np.all(noisy_scan >= 0)
    assert np.all(noisy_scan <= lidar.max_range)


def test_lidar_advanced_noise():
    """高度なノイズモデル"""
    world = PhysicsWorld()
    lidar = LiDARSensor(world.world)

    clean_scan = np.ones(72) * 5.0

    # 高度なノイズ
    noisy_scan = lidar.add_advanced_noise(
        clean_scan, noise_level=0.05, dropout_prob=0.1, spike_prob=0.05
    )

    # ノイズが追加されている
    assert not np.allclose(clean_scan, noisy_scan)

    # 範囲内
    assert np.all(noisy_scan >= 0)
    assert np.all(noisy_scan <= lidar.max_range)

    # ドロップアウトによりmax_rangeの値が増えているはず
    num_max = np.sum(noisy_scan == lidar.max_range)
    assert num_max > 0


def test_lidar_range_limits():
    """測定範囲の制限"""
    world = PhysicsWorld()

    # 非常に遠くに壁を配置（max_rangeを超える）
    world.add_wall_segment((50, -10), (50, 10))

    lidar = LiDARSensor(world.world, num_rays=72, max_range=10.0)
    distances = lidar.scan(position=(0, 0), orientation=0)

    # max_rangeでクリップされる
    assert np.all(distances <= lidar.max_range)
