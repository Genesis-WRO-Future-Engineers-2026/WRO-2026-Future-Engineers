"""適応的学習スクリプト

カリキュラム学習 + 適応的報酬スケーリング + 学習監視を統合した
安定性重視の学習スクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import argparse
import torch
from datetime import datetime
from pathlib import Path

from src.env.minicar_env import MinicarEnv
from src.rl.ppo import PPO
from src.rl.trainer import PPOTrainer
from src.rl.adaptive_reward import AdaptiveRewardScaler
from src.curriculum.curriculum_manager import CurriculumManager
from src.utils.logger import create_logger
from src.domain_randomization import get_config


def parse_args():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(
        description="Adaptive PPO Training for Minicar (Curriculum + Adaptive Reward)"
    )

    # 基本設定
    parser.add_argument(
        "--max-steps",
        type=int,
        default=2000,
        help="Maximum steps per episode",
    )
    parser.add_argument(
        "--total-iterations",
        type=int,
        default=2000,
        help="Total training iterations",
    )

    # 学習設定
    parser.add_argument(
        "--n-steps",
        type=int,
        default=2048,
        help="Number of steps per iteration",
    )
    parser.add_argument(
        "--n-epochs", type=int, default=10, help="Number of epochs per update"
    )
    parser.add_argument(
        "--batch-size", type=int, default=64, help="Batch size"
    )

    # PPOパラメータ
    parser.add_argument(
        "--lr", type=float, default=3e-4, help="Learning rate"
    )
    parser.add_argument(
        "--gamma", type=float, default=0.99, help="Discount factor"
    )
    parser.add_argument(
        "--gae-lambda", type=float, default=0.95, help="GAE lambda"
    )
    parser.add_argument(
        "--clip-range", type=float, default=0.2, help="PPO clip range"
    )
    parser.add_argument(
        "--entropy-coef",
        type=float,
        default=0.01,
        help="Entropy coefficient",
    )
    parser.add_argument(
        "--value-coef", type=float, default=0.5, help="Value coefficient"
    )
    parser.add_argument(
        "--max-grad-norm",
        type=float,
        default=0.5,
        help="Max gradient norm",
    )
    parser.add_argument(
        "--reward-clip",
        type=float,
        default=10.0,
        help="Reward clipping range",
    )

    # ネットワーク設定
    parser.add_argument(
        "--hidden-dims",
        type=int,
        nargs="+",
        default=[256, 256],
        help="Hidden layer dimensions",
    )
    parser.add_argument(
        "--use-shared-network",
        action="store_true",
        help="Use shared network for actor-critic",
    )

    # カリキュラム学習設定
    parser.add_argument(
        "--curriculum-success-threshold",
        type=float,
        default=0.8,
        help="Success rate threshold for curriculum level up",
    )
    parser.add_argument(
        "--curriculum-min-episodes",
        type=int,
        default=50,
        help="Minimum episodes before curriculum level change",
    )

    # 適応的報酬スケーリング設定
    parser.add_argument(
        "--disable-adaptive-reward",
        action="store_true",
        help="Disable adaptive reward scaling (use fixed v3.2 coefficients)",
    )

    # チェックポイント
    parser.add_argument(
        "--save-freq",
        type=int,
        default=50,
        help="Save frequency (iterations)",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="models/checkpoints_adaptive",
        help="Checkpoint directory",
    )
    parser.add_argument(
        "--resume", type=str, default=None, help="Resume from checkpoint"
    )

    # 評価
    parser.add_argument(
        "--eval-freq",
        type=int,
        default=25,
        help="Evaluation frequency (iterations)",
    )
    parser.add_argument(
        "--n-eval-episodes",
        type=int,
        default=10,
        help="Number of evaluation episodes",
    )

    # ロギング
    parser.add_argument(
        "--log-dir", type=str, default="logs", help="Log directory"
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        default=None,
        help="Experiment name",
    )
    parser.add_argument(
        "--no-tensorboard",
        action="store_true",
        help="Disable TensorBoard logging",
    )

    # その他
    parser.add_argument(
        "--seed", type=int, default=None, help="Random seed"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Device (cpu, cuda, mps, or auto)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Enable GUI visualization",
    )

    return parser.parse_args()


def get_device(device_str: str) -> torch.device:
    """デバイスを取得"""
    if device_str == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")
    else:
        return torch.device(device_str)


def main():
    """メイン関数"""
    args = parse_args()

    # デバイス
    device = get_device(args.device)
    print(f"Using device: {device}")

    # シード設定
    if args.seed is not None:
        torch.manual_seed(args.seed)
        import numpy as np
        np.random.seed(args.seed)
        print(f"Random seed: {args.seed}")

    # 実験名の自動生成
    if args.experiment_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.experiment_name = f"adaptive_curriculum_{timestamp}"

    print(f"Experiment: {args.experiment_name}")

    # カリキュラム学習のコース設定
    curriculum_courses = [
        "courses/curriculum/level0_straight.json",      # Level 0: 直線
        "courses/curriculum/level1_simple_curve.json",  # Level 1: 単純カーブ
        "courses/curriculum/level2_s_curve.json",       # Level 2: S字
        "courses/curriculum/level3_small_oval.json",    # Level 3: 小オーバル
        "courses/easy/simple_oval.json",                # Level 4: オーバル
        "courses/real-course/real-course.json",         # Level 5: 実コース
    ]

    # カリキュラムマネージャーの作成
    curriculum = CurriculumManager(
        courses=curriculum_courses,
        success_threshold=args.curriculum_success_threshold,
        degradation_threshold=0.3,
        evaluation_window=100,
        min_episodes_before_advance=args.curriculum_min_episodes,
        allow_degradation=True,
    )

    print("\n" + "="*60)
    print("CURRICULUM LEARNING ENABLED")
    print(f"Total Levels: {len(curriculum_courses)}")
    for i, course in enumerate(curriculum_courses):
        print(f"  Level {i}: {Path(course).name}")
    print("="*60 + "\n")

    # 適応的報酬スケーラーの作成
    if not args.disable_adaptive_reward:
        adaptive_reward_scaler = AdaptiveRewardScaler(
            initial_phase=0,
            enable_auto_phase_transition=True,
        )
        print("ADAPTIVE REWARD SCALING ENABLED")
        print(f"  Initial Phase: {adaptive_reward_scaler.phase}")
        print(f"  Auto Transition: {adaptive_reward_scaler.enable_auto_phase_transition}")
        print("="*60 + "\n")
    else:
        adaptive_reward_scaler = None
        print("ADAPTIVE REWARD SCALING DISABLED (using fixed v3.2 coefficients)")

    # Domain Randomization設定
    dr_config = get_config('disabled')

    # 環境の作成（最初のコースから開始）
    render_mode = "human" if args.gui else None
    if args.gui:
        print("GUI visualization enabled")

    env = MinicarEnv(
        course_file=curriculum.get_current_course(),
        render_mode=render_mode,
        max_steps=args.max_steps,
        enable_domain_randomization=False,
        physics_randomization_config=dr_config['physics'],
        sensor_noise_config=dr_config['sensor'],
        adaptive_reward_scaler=adaptive_reward_scaler,
    )

    # PPOの作成
    ppo = PPO(
        obs_dim=env.observation_space.shape[0],
        action_dim=env.action_space.shape[0],
        device=device,
        hidden_dims=tuple(args.hidden_dims),
        use_shared_network=args.use_shared_network,
        learning_rate=args.lr,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
        clip_range=args.clip_range,
        entropy_coef=args.entropy_coef,
        value_coef=args.value_coef,
        max_grad_norm=args.max_grad_norm,
    )

    # チェックポイントから再開
    if args.resume is not None:
        ppo.load(args.resume)
        print(f"Resumed from checkpoint: {args.resume}")

    # ロガーの作成
    logger = create_logger(
        log_dir=args.log_dir,
        experiment_name=args.experiment_name,
        use_tensorboard=not args.no_tensorboard,
        use_csv=True,
    )

    # ハイパーパラメータをログ
    hparams = vars(args)
    hparams["device"] = str(device)
    hparams["curriculum_levels"] = len(curriculum_courses)
    hparams["adaptive_reward_enabled"] = not args.disable_adaptive_reward
    logger.log_hyperparams(hparams)

    # Trainerの作成（カリキュラム学習対応）
    trainer = PPOTrainer(
        env=env,
        ppo=ppo,
        logger=logger,
        n_steps=args.n_steps,
        n_epochs=args.n_epochs,
        batch_size=args.batch_size,
        reward_clip=args.reward_clip,
        save_freq=args.save_freq,
        checkpoint_dir=args.checkpoint_dir,
        eval_freq=args.eval_freq,
        n_eval_episodes=args.n_eval_episodes,
        curriculum=curriculum,
    )

    # 学習開始
    print("\n" + "="*60)
    print("TRAINING START")
    print("="*60)

    try:
        trainer.train(total_iterations=args.total_iterations)
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
    finally:
        # ログを保存して閉じる
        logger.save()
        logger.close()
        env.close()

    print("\n" + "="*60)
    print("TRAINING FINISHED")
    print("="*60)

    # 最終統計
    print("\nFinal Statistics:")
    curriculum_stats = curriculum.get_stats()
    print(f"  Final Level: {curriculum_stats['current_level']}/{curriculum_stats['total_courses']-1}")
    print(f"  Final Course: {Path(curriculum_stats['current_course']).name}")
    print(f"  Total Episodes: {curriculum_stats['total_episodes']}")
    print(f"  Success Rate: {curriculum_stats['success_rate']:.2%}")

    if adaptive_reward_scaler is not None:
        phase_info = adaptive_reward_scaler.get_phase_info()
        print(f"\n  Reward Phase: {phase_info['reward_phase']}")
        print(f"  Episodes in Phase: {phase_info['episodes_in_phase']}")


if __name__ == "__main__":
    main()
