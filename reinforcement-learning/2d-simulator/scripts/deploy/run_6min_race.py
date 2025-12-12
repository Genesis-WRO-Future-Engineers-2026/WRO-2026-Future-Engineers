"""本番環境用6分間連続走行スクリプト

本番競技会での使用を想定:
- 6分間連続で周回走行
- 衝突時は初期位置からリスタート
- ゴール到達時はチェックポイントをリセットして次の周回へ
- 最速3周のラップタイムを記録
"""

import sys
import time
import argparse
from pathlib import Path

import torch
import numpy as np

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.env.minicar_env import MinicarEnv
from src.rl.ppo import PPO


def run_6min_race(
    model_path: str,
    course_file: str = "courses/competition/real_course.json",
    duration: int = 360,  # 6分
    gui: bool = False,
):
    """6分間連続走行を実行

    Args:
        model_path: 学習済みモデルのパス
        course_file: コース定義ファイル
        duration: 走行時間（秒）
        gui: GUI表示するかどうか
    """
    print("=" * 60)
    print("6分間連続走行レース")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Course: {course_file}")
    print(f"Duration: {duration}秒")
    print(f"GUI: {gui}")
    print("=" * 60)

    # 環境作成（deployment_mode=True）
    render_mode = "human" if gui else None
    env = MinicarEnv(
        course_file=course_file,
        render_mode=render_mode,
        max_steps=100000,  # 十分に大きな値
        deployment_mode=True,  # ゴール到達で終了しない
    )

    # モデルロード
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    obs_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]

    agent = PPO(
        obs_dim=obs_dim,
        action_dim=action_dim,
        hidden_dim=64,
        learning_rate=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        entropy_coef=0.01,
        device=device,
    )

    print(f"Loading model from {model_path}...")
    checkpoint = torch.load(model_path, map_location=device)
    agent.policy.load_state_dict(checkpoint["policy_state_dict"])
    agent.policy.eval()
    print("Model loaded successfully!")

    # レース開始
    obs, info = env.reset()
    start_time = time.time()
    lap_times = []  # ラップタイム記録
    current_lap_start = start_time
    total_steps = 0
    collision_count = 0

    print("\n" + "=" * 60)
    print("レース開始！")
    print("=" * 60)

    while time.time() - start_time < duration:
        # 行動選択
        with torch.no_grad():
            obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(device)
            action, _ = agent.policy.get_action(obs_tensor, deterministic=True)
            action = action.cpu().numpy()[0]

        # ステップ実行
        obs, reward, terminated, truncated, info = env.step(action)
        total_steps += 1

        # ゴール到達判定（チェックポイントを全て通過している場合）
        checkpoints = env.course.get_checkpoints()
        if env.next_checkpoint_index >= len(checkpoints):
            if env.course.check_goal(info["position"]):
                # ラップタイム記録
                lap_time = time.time() - current_lap_start
                lap_times.append(lap_time)
                print(f"  Lap {len(lap_times)}: {lap_time:.2f}秒")

                # 次の周回へ
                env.next_checkpoint_index = 0
                current_lap_start = time.time()

        # 衝突時はリスタート
        if terminated:
            collision_count += 1
            print(f"  衝突 ({collision_count}回目) - リスタート")
            obs, info = env.reset()
            current_lap_start = time.time()  # ラップタイムもリセット

        # GUI描画
        if gui:
            env.render()

        # 経過時間表示（10秒ごと）
        elapsed = time.time() - start_time
        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
            remaining = duration - elapsed
            if int(remaining) % 10 == 0:
                print(f"  経過: {elapsed:.0f}秒 / 残り: {remaining:.0f}秒")

    # レース終了
    env.close()

    print("\n" + "=" * 60)
    print("レース終了！")
    print("=" * 60)
    print(f"総走行時間: {duration}秒")
    print(f"総ステップ数: {total_steps}")
    print(f"衝突回数: {collision_count}")
    print(f"完走周回数: {len(lap_times)}")

    if lap_times:
        print(f"\nラップタイム:")
        for i, lap_time in enumerate(lap_times, 1):
            print(f"  Lap {i}: {lap_time:.2f}秒")

        # 最速3周の合計タイム（スコア）
        if len(lap_times) >= 3:
            fastest_3_laps = sorted(lap_times)[:3]
            score = sum(fastest_3_laps)
            print(f"\n最速3周の合計タイム（スコア）: {score:.2f}秒")
            print(f"  1位: {fastest_3_laps[0]:.2f}秒")
            print(f"  2位: {fastest_3_laps[1]:.2f}秒")
            print(f"  3位: {fastest_3_laps[2]:.2f}秒")
        else:
            print(f"\n完走周回数が3未満のため、スコアなし")
    else:
        print("\nゴール到達なし")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="6分間連続走行レース（本番環境想定）"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="学習済みモデルのパス",
    )
    parser.add_argument(
        "--course",
        type=str,
        default="courses/competition/real_course.json",
        help="コース定義ファイル",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=360,
        help="走行時間（秒）デフォルト: 360（6分）",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="GUI表示を有効にする",
    )

    args = parser.parse_args()

    run_6min_race(
        model_path=args.model,
        course_file=args.course,
        duration=args.duration,
        gui=args.gui,
    )


if __name__ == "__main__":
    main()
