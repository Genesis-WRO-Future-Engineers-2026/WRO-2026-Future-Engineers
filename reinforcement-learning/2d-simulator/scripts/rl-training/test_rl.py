"""強化学習モジュールの簡単な動作確認"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
import numpy as np

from src.env.minicar_env import MinicarEnv
from src.rl.policy import GaussianPolicy
from src.rl.value import ValueNetwork
from src.rl.buffer import RolloutBuffer
from src.rl.ppo import PPO


def test_policy_network():
    """ポリシーネットワークのテスト"""
    print("=" * 60)
    print("Testing Policy Network...")
    print("=" * 60)

    policy = GaussianPolicy(obs_dim=77, action_dim=2)
    obs = torch.randn(4, 77)  # バッチサイズ4

    # 順伝播
    mean, std = policy(obs)
    print(f"Mean shape: {mean.shape}")
    print(f"Std shape: {std.shape}")

    # 行動取得
    action, log_prob, mean_out = policy.get_action(obs)
    print(f"Action shape: {action.shape}")
    print(f"Log prob shape: {log_prob.shape}")
    print(f"Action range: steering [{action[:, 0].min():.3f}, {action[:, 0].max():.3f}], throttle [{action[:, 1].min():.3f}, {action[:, 1].max():.3f}]")

    print("✓ Policy network test passed!\n")


def test_value_network():
    """価値関数ネットワークのテスト"""
    print("=" * 60)
    print("Testing Value Network...")
    print("=" * 60)

    value_net = ValueNetwork(obs_dim=77)
    obs = torch.randn(4, 77)

    # 順伝播
    value = value_net(obs)
    print(f"Value shape: {value.shape}")
    print(f"Value range: [{value.min():.3f}, {value.max():.3f}]")

    print("✓ Value network test passed!\n")


def test_rollout_buffer():
    """ロールアウトバッファのテスト"""
    print("=" * 60)
    print("Testing Rollout Buffer...")
    print("=" * 60)

    buffer = RolloutBuffer(
        buffer_size=100,
        obs_dim=77,
        action_dim=2,
        gamma=0.99,
        gae_lambda=0.95,
    )

    # データを追加
    for i in range(100):
        obs = np.random.randn(77)
        action = np.random.randn(2)
        reward = np.random.randn()
        value = np.random.randn()
        log_prob = np.random.randn()
        done = i % 20 == 19  # 20ステップごとに終了

        buffer.add(obs, action, reward, value, log_prob, done)

    # アドバンテージとリターンを計算
    last_value = 0.0
    buffer.compute_returns_and_advantages(last_value)

    print(f"Buffer size: {buffer.size()}")
    print(f"Advantages mean: {buffer.advantages.mean():.3f}")
    print(f"Returns mean: {buffer.returns.mean():.3f}")

    # ミニバッチ取得
    batch_count = 0
    for batch in buffer.get(batch_size=32):
        batch_count += 1
        print(f"Batch {batch_count}: obs shape {batch['observations'].shape}")

    print("✓ Rollout buffer test passed!\n")


def test_ppo():
    """PPOのテスト"""
    print("=" * 60)
    print("Testing PPO...")
    print("=" * 60)

    # デバイス
    device = torch.device("cpu")

    # PPOの作成
    ppo = PPO(
        obs_dim=77,
        action_dim=2,
        device=device,
        use_shared_network=False,
    )

    # 行動取得
    obs = np.random.randn(77)
    action, log_prob, value = ppo.get_action(obs)

    print(f"Action: {action}")
    print(f"Log prob: {log_prob:.3f}")
    print(f"Value: {value:.3f}")

    # バッファの作成
    buffer = RolloutBuffer(
        buffer_size=128,
        obs_dim=77,
        action_dim=2,
        device=device,
        gamma=0.99,
        gae_lambda=0.95,
    )

    # データを追加
    for i in range(128):
        obs = np.random.randn(77)
        action, log_prob, value = ppo.get_action(obs)
        reward = np.random.randn()
        done = i % 20 == 19

        buffer.add(obs, action, reward, value, log_prob, done)

    buffer.compute_returns_and_advantages(0.0)

    # PPO更新
    print("Running PPO update...")
    logs = ppo.update(buffer, n_epochs=2, batch_size=32)

    print("Update logs:")
    for key, value in logs.items():
        print(f"  {key}: {value:.4f}")

    print("✓ PPO test passed!\n")


def test_with_env():
    """環境との統合テスト"""
    print("=" * 60)
    print("Testing with Environment...")
    print("=" * 60)

    # 環境の作成
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")

    # PPOの作成
    device = torch.device("cpu")
    ppo = PPO(
        obs_dim=env.observation_space.shape[0],
        action_dim=env.action_space.shape[0],
        device=device,
    )

    # 1エピソード実行
    obs, _ = env.reset()
    total_reward = 0
    steps = 0

    for _ in range(100):
        action, _, _ = ppo.get_action(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        steps += 1

        if terminated or truncated:
            break

    print(f"Episode finished in {steps} steps")
    print(f"Total reward: {total_reward:.2f}")
    print(f"Final position: {info['position']}")
    print(f"Checkpoints passed: {info['next_checkpoint_index']}/{info['total_checkpoints']}")

    env.close()

    print("✓ Environment integration test passed!\n")


def main():
    """メイン関数"""
    print("\n" + "=" * 60)
    print("PPO Implementation Test Suite")
    print("=" * 60 + "\n")

    try:
        test_policy_network()
        test_value_network()
        test_rollout_buffer()
        test_ppo()
        test_with_env()

        print("=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
