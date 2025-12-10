"""保存されたモデルのテスト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
import numpy as np

from src.env.minicar_env import MinicarEnv
from src.rl.ppo import PPO


def test_saved_model(model_path: str, n_episodes: int = 3, render: bool = False):
    """
    保存されたモデルをテスト

    Args:
        model_path: モデルファイルのパス
        n_episodes: テストエピソード数
        render: GUIで描画するかどうか
    """
    print("=" * 60)
    print(f"Testing saved model: {model_path}")
    print("=" * 60)

    # デバイス
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}\n")

    # 環境の作成
    render_mode = "human" if render else None
    print(f"[DEBUG] Creating environment with render_mode={render_mode}")
    env = MinicarEnv(course_file="courses/easy/simple_oval.json", render_mode=render_mode)
    print(f"[DEBUG] Environment created, render_mode={env.render_mode}")

    # PPOの作成
    ppo = PPO(
        obs_dim=env.observation_space.shape[0],
        action_dim=env.action_space.shape[0],
        device=device,
    )

    # モデルの読み込み
    ppo.load(model_path)
    print(f"✓ Model loaded successfully\n")

    # テスト実行
    episode_rewards = []
    episode_lengths = []
    checkpoints_passed_list = []

    for episode in range(n_episodes):
        obs, _ = env.reset()
        episode_reward = 0
        episode_length = 0
        done = False

        while not done:
            # 決定的に行動を取得
            action, _, _ = ppo.get_action(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            episode_reward += reward
            episode_length += 1

            # 描画
            if render:
                if episode_length == 1:  # 最初のステップだけログ
                    print(f"[DEBUG] Calling env.render() for episode {episode + 1}")
                env.render()

            # 最大ステップ数でbreak
            if episode_length >= 1000:
                break

        episode_rewards.append(episode_reward)
        episode_lengths.append(episode_length)
        checkpoints_passed_list.append(info["checkpoints_passed"])

        print(f"Episode {episode + 1}:")
        print(f"  Reward: {episode_reward:.2f}")
        print(f"  Length: {episode_length}")
        print(f"  Checkpoints: {info['checkpoints_passed']}")
        print(f"  Final position: ({info['position'][0]:.2f}, {info['position'][1]:.2f})")
        print(f"  Final speed: {info['speed']:.2f} m/s")
        print()

    # 統計
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"Average Reward: {np.mean(episode_rewards):.2f} ± {np.std(episode_rewards):.2f}")
    print(f"Average Length: {np.mean(episode_lengths):.1f} ± {np.std(episode_lengths):.1f}")
    print(f"Average Checkpoints: {np.mean(checkpoints_passed_list):.1f} ± {np.std(checkpoints_passed_list):.1f}")
    print("=" * 60)

    env.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        default="models/checkpoints/final_model.pth",
        help="Path to model file",
    )
    parser.add_argument(
        "--n-episodes",
        type=int,
        default=3,
        help="Number of test episodes",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Enable GUI rendering",
    )
    args = parser.parse_args()

    test_saved_model(args.model, args.n_episodes, args.render)
