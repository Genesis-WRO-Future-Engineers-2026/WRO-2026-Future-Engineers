"""PPO学習スクリプト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import torch
from datetime import datetime

from src.env.minicar_env import MinicarEnv
from src.rl.ppo import PPO
from src.rl.trainer import PPOTrainer
from src.utils.logger import create_logger


def parse_args():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(description="PPO Training for Minicar")

    # 環境設定
    parser.add_argument(
        "--course",
        type=str,
        default="courses/easy/simple_oval.json",
        help="Course file path",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=2000,
        help="Maximum steps per episode",
    )

    # 学習設定
    parser.add_argument(
        "--total-iterations",
        type=int,
        default=1000,
        help="Total training iterations",
    )
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
        "--clip-range-vf",
        type=float,
        default=None,
        help="Value function clip range (None to disable clipping)",
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
        help="Reward clipping range (to prevent gradient explosion)",
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
        default="models/checkpoints",
        help="Checkpoint directory",
    )
    parser.add_argument(
        "--resume", type=str, default=None, help="Resume from checkpoint"
    )

    # 評価
    parser.add_argument(
        "--eval-freq",
        type=int,
        default=50,
        help="Evaluation frequency (iterations)",
    )
    parser.add_argument(
        "--n-eval-episodes",
        type=int,
        default=5,
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
        help="Experiment name (auto-generated if not specified)",
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
        help="Enable GUI visualization during training",
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
        course_name = os.path.basename(args.course).replace(".json", "")
        args.experiment_name = f"ppo_{course_name}_{timestamp}"

    print(f"Experiment: {args.experiment_name}")

    # 環境の作成
    render_mode = "human" if args.gui else None
    if args.gui:
        print("GUI visualization enabled")

    env = MinicarEnv(
        course_file=args.course,
        render_mode=render_mode,
        max_steps=args.max_steps,
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
        clip_range_vf=args.clip_range_vf,
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
    logger.log_hyperparams(hparams)

    # Trainerの作成
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
    )

    # 学習開始
    try:
        trainer.train(total_iterations=args.total_iterations)
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
    finally:
        # ログを保存して閉じる
        logger.save()
        logger.close()
        env.close()

    print("Training finished!")


if __name__ == "__main__":
    main()
