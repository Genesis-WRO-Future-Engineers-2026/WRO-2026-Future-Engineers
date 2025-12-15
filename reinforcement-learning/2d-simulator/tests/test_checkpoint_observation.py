"""チェックポイント観測のテスト

NOTE: Sim2Real対応により、観測空間からチェックポイント情報を削除しました。
このテストファイルは将来の参考のため残していますが、すべてスキップされます。
"""

import pytest
import numpy as np
from src.env.minicar_env import MinicarEnv

pytestmark = pytest.mark.skip(reason="観測空間からチェックポイント情報を削除（Sim2Real対応）")


def test_checkpoint_distance_calculation():
    """チェックポイント距離の計算が正しいか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, _ = env.reset()

    # 観測空間が12次元であることを確認
    assert obs.shape == (12,), f"Expected shape (12,), got {obs.shape}"

    # チェックポイント距離が正の値であることを確認
    checkpoint_distance = obs[10]
    assert checkpoint_distance > 0, f"Distance should be positive, got {checkpoint_distance}"

    env.close()


def test_checkpoint_angle_range():
    """チェックポイント角度が適切な範囲にあるか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, _ = env.reset()

    # チェックポイント角度が -π ~ π の範囲内であることを確認
    checkpoint_angle = obs[11]
    assert -np.pi <= checkpoint_angle <= np.pi, \
        f"Angle should be in [-π, π], got {checkpoint_angle}"

    env.close()


def test_checkpoint_info_updates():
    """ステップごとにチェックポイント情報が更新されるか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs1, _ = env.reset()

    # 1ステップ実行
    action = env.action_space.sample()
    obs2, _, _, _, _ = env.step(action)

    # チェックポイント情報が変化していることを確認
    distance1 = obs1[10]
    distance2 = obs2[10]

    # 移動したので距離が変わっているはず
    # （同じ場所に留まる可能性もあるので、単に値が存在することを確認）
    assert isinstance(distance2, (int, float, np.floating))

    # 観測空間のサイズが維持されていることを確認
    assert obs2.shape == (12,), f"Expected shape (12,), got {obs2.shape}"

    env.close()


def test_checkpoint_switches_to_goal():
    """全チェックポイント通過後、ゴールが目標になるか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, _ = env.reset()

    # 強制的に全チェックポイントを通過済みにする
    checkpoints = env.course.get_checkpoints()
    env.next_checkpoint_index = len(checkpoints)

    # 観測を再取得
    distance, angle = env._get_next_checkpoint_info()

    # ゴールまでの距離が計算されていることを確認
    goal_pos, _ = env.course.get_goal_info()
    vehicle_pos = env._cached_vehicle_state["position"]
    expected_distance = np.sqrt(
        (goal_pos[0] - vehicle_pos[0])**2 +
        (goal_pos[1] - vehicle_pos[1])**2
    )

    assert abs(distance - expected_distance) < 1e-5, \
        f"Expected distance to goal {expected_distance}, got {distance}"

    env.close()


def test_observation_space_consistency():
    """観測空間のサイズが一貫しているか"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")

    # リセット時
    obs, _ = env.reset()
    assert obs.shape == (12,), f"Expected shape (12,) at reset, got {obs.shape}"

    # 複数ステップ実行
    for _ in range(10):
        action = env.action_space.sample()
        obs, _, terminated, truncated, _ = env.step(action)
        assert obs.shape == (12,), f"Expected shape (12,) during step, got {obs.shape}"

        if terminated or truncated:
            obs, _ = env.reset()
            assert obs.shape == (12,), f"Expected shape (12,) after reset, got {obs.shape}"

    env.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
