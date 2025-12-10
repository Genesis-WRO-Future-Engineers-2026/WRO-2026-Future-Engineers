"""MinicarEnvのテスト"""

import pytest
import numpy as np
from src.env.minicar_env import MinicarEnv


def test_env_creation():
    """環境が正しく作成されるか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    assert env is not None


def test_env_reset():
    """環境リセットのテスト"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, info = env.reset()

    # 観測の形状確認
    assert obs.shape == (77,)
    assert isinstance(info, dict)
    assert "position" in info
    assert "speed" in info


def test_env_step():
    """ステップ実行のテスト"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    env.reset()

    # まっすぐ前進
    action = np.array([0.0, 0.5])
    obs, reward, terminated, truncated, info = env.step(action)

    # 戻り値の型確認
    assert obs.shape == (77,)
    assert isinstance(reward, (int, float))
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_action_space():
    """行動空間のテスト"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")

    # 行動空間の形状
    assert env.action_space.shape == (2,)

    # サンプリング
    action = env.action_space.sample()
    assert len(action) == 2
    assert -1.0 <= action[0] <= 1.0  # steering
    assert 0.0 <= action[1] <= 1.0  # throttle


def test_observation_space():
    """観測空間のテスト"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")

    # 観測空間の形状
    assert env.observation_space.shape == (77,)


def test_multiple_episodes():
    """複数エピソードの実行"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")

    for episode in range(3):
        obs, info = env.reset()
        done = False
        steps = 0

        while not done and steps < 100:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            steps += 1

        # エピソードが完了したことを確認
        assert steps > 0


def test_checkpoint_passing():
    """チェックポイント通過のテスト"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    env.reset()

    initial_checkpoints = 0

    # 前進を続ける
    for _ in range(500):
        action = np.array([0.0, 0.8])  # まっすぐ前進
        obs, reward, terminated, truncated, info = env.step(action)

        if info["checkpoints_passed"] > initial_checkpoints:
            # チェックポイント通過を確認
            assert info["checkpoints_passed"] >= 1
            break

        if terminated or truncated:
            break


def test_collision_detection():
    """衝突検出のテスト"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    env.reset()

    # 壁に向かって全速力
    for _ in range(200):
        action = np.array([1.0, 1.0])  # 右旋回＋全速力
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated:
            # 衝突で終了したか確認
            assert info["min_distance"] < 0.5
            break


def test_observation_bounds():
    """観測値の範囲確認"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, info = env.reset()

    # LiDARの範囲（0〜max_range）
    lidar_data = obs[:72]
    assert np.all(lidar_data >= 0)
    assert np.all(lidar_data <= 10.0)  # max_range

    # 数ステップ実行
    for _ in range(10):
        action = np.array([0.0, 0.5])
        obs, reward, terminated, truncated, info = env.step(action)

        lidar_data = obs[:72]
        assert np.all(lidar_data >= 0)
        assert np.all(lidar_data <= 10.0)
