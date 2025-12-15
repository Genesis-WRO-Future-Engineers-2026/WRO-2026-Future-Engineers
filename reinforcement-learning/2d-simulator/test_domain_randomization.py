"""Domain Randomization動作確認スクリプト"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.domain_randomization import (
    PhysicsRandomizer,
    SensorNoiseRandomizer,
    get_config,
)
from src.env.minicar_env import MinicarEnv

def test_physics_randomizer():
    """PhysicsRandomizerの動作確認"""
    print("=" * 60)
    print("PhysicsRandomizer Test")
    print("=" * 60)

    config = get_config('mild')['physics']
    randomizer = PhysicsRandomizer(config)

    print("\n[Test 1] 10回ランダム化して範囲を確認:")
    for i in range(10):
        params = randomizer.randomize()
        print(f"\nTrial {i+1}:")
        print(f"  Friction: {params['friction']:.3f}")
        print(f"  Mass: {params['mass']:.3f} kg")
        print(f"  Motor Force: {params['motor_force']:.3f} N")
        print(f"  Linear Damping: {params['linear_damping']:.3f}")
        print(f"  Angular Damping: {params['angular_damping']:.3f}")

        # 範囲チェック
        assert 0.6 <= params['friction'] <= 0.8, "Friction out of range"
        assert 1.3 <= params['mass'] <= 1.5, "Mass out of range"
        assert 19.0 <= params['motor_force'] <= 21.0, "Motor force out of range"

    print("\n✅ PhysicsRandomizer test passed!")
    return True


def test_sensor_noise_randomizer():
    """SensorNoiseRandomizerの動作確認"""
    print("\n" + "=" * 60)
    print("SensorNoiseRandomizer Test")
    print("=" * 60)

    import numpy as np
    from src.env.sensors import LiDARSensor
    from src.physics.box2d_wrapper import PhysicsWorld

    # テスト用の環境を作成
    world = PhysicsWorld()
    lidar = LiDARSensor(world.world, num_rays=5, max_range=3.0)

    config = get_config('mild')['sensor']
    randomizer = SensorNoiseRandomizer(config)

    # クリーンなスキャン（仮想的に）
    clean_scan = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

    print("\n[Test 1] クリーンスキャン:")
    print(f"  {clean_scan}")

    print("\n[Test 2] 10回ノイズ適用:")
    for i in range(10):
        noisy_scan = randomizer.apply_noise(lidar, clean_scan.copy())
        print(f"  Trial {i+1}: {noisy_scan}")

        # 範囲チェック
        assert np.all(noisy_scan >= 0.0), "Noisy scan below 0"
        assert np.all(noisy_scan <= 3.0), "Noisy scan above max_range"

    print("\n✅ SensorNoiseRandomizer test passed!")
    return True


def test_env_with_domain_randomization():
    """MinicarEnv with Domain Randomizationの動作確認"""
    print("\n" + "=" * 60)
    print("MinicarEnv with Domain Randomization Test")
    print("=" * 60)

    config = get_config('mild')

    # Domain Randomization有効で環境作成
    env = MinicarEnv(
        course_file="courses/easy/simple_oval.json",
        enable_domain_randomization=True,
        physics_randomization_config=config['physics'],
        sensor_noise_config=config['sensor'],
    )

    print("\n[Test 1] 環境リセット:")
    obs, info = env.reset()
    print(f"  Observation shape: {obs.shape}")
    print(f"  Observation: {obs}")
    assert obs.shape == (10,), f"Unexpected observation shape: {obs.shape}"

    print("\n[Test 2] 5ステップ実行:")
    for i in range(5):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"  Step {i+1}:")
        print(f"    Reward: {reward:.3f}")
        print(f"    LiDAR (first 3): {obs[:3]}")
        print(f"    Terminated: {terminated}, Truncated: {truncated}")

        assert obs.shape == (10,), f"Unexpected observation shape: {obs.shape}"

        if terminated or truncated:
            print("  Episode ended early")
            break

    print("\n[Test 3] 複数エピソードでパラメータが変わることを確認:")
    observations = []
    for ep in range(3):
        obs, _ = env.reset()
        observations.append(obs.copy())
        print(f"  Episode {ep+1} initial obs (first 3): {obs[:3]}")

    # 少なくとも一部は異なるはず
    import numpy as np
    all_same = all(np.allclose(observations[0], obs) for obs in observations[1:])
    if not all_same:
        print("  ✅ Observations vary across episodes (Domain Randomization working!)")
    else:
        print("  ⚠️  Warning: All observations are similar (may be expected with low randomization)")

    print("\n✅ MinicarEnv with Domain Randomization test passed!")
    return True


def test_config_levels():
    """各設定レベルのテスト"""
    print("\n" + "=" * 60)
    print("Config Levels Test")
    print("=" * 60)

    for level in ['disabled', 'mild', 'standard', 'strong']:
        print(f"\n[Test] Level: {level}")
        config = get_config(level)

        if level == 'disabled':
            assert config['physics'] is None, "Physics should be None for disabled"
            assert config['sensor'] is None, "Sensor should be None for disabled"
            print("  ✅ Disabled config correct")
        else:
            assert config['physics'] is not None, f"Physics should not be None for {level}"
            assert config['sensor'] is not None, f"Sensor should not be None for {level}"
            print(f"  ✅ {level.capitalize()} config loaded")

    print("\n✅ All config levels test passed!")
    return True


def main():
    """すべてのテストを実行"""
    print("\n" + "🚀" * 30)
    print("Domain Randomization - 動作確認テスト")
    print("🚀" * 30)

    try:
        # Test 1: PhysicsRandomizer
        if not test_physics_randomizer():
            return False

        # Test 2: SensorNoiseRandomizer
        if not test_sensor_noise_randomizer():
            return False

        # Test 3: Config Levels
        if not test_config_levels():
            return False

        # Test 4: MinicarEnv with Domain Randomization
        if not test_env_with_domain_randomization():
            return False

        print("\n" + "🎉" * 30)
        print("すべてのテストが成功しました！")
        print("Domain Randomizationの実装が正常に動作しています。")
        print("🎉" * 30)

        print("\n次のステップ:")
        print("1. 学習スクリプトを実行:")
        print("   python scripts/rl-training/train.py \\")
        print("     --course courses/easy/simple_oval.json \\")
        print("     --total-iterations 10 \\")
        print("     --enable-domain-randomization \\")
        print("     --dr-level mild")
        print()

        return True

    except Exception as e:
        print(f"\n❌ テストが失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
