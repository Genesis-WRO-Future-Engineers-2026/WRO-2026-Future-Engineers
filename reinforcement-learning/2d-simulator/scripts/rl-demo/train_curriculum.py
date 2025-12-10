"""カリキュラム学習を用いたPPO学習スクリプト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import argparse
import torch
import yaml
from datetime import datetime
from pathlib import Path

from src.env.minicar_env import MinicarEnv
from src.rl.ppo import PPO
from src.rl.trainer import PPOTrainer
from src.curriculum.curriculum_manager import CurriculumManager
from src.utils.logger import create_logger


def parse_args():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(
        description="PPO Training with Curriculum Learning for Minicar"
    )

    # 設定ファイル
    parser.add_argument(
        "--config",
        type=str,
        default="configs/ppo_curriculum.yaml",
        help="Config file path",
    )

    # 上書き設定
    parser.add_argument(
        "--total-iterations",
        type=int,
        default=None,
        help="Total training iterations (overrides config)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Enable GUI visualization during training",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device (cpu, cuda, mps, or auto) (overrides config)",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Random seed (overrides config)"
    )
    parser.add_argument(
        "--resume", type=str, default=None, help="Resume from checkpoint"
    )

    return parser.parse_args()


def load_config(config_path: str) -> dict:
    """設定ファイルを読み込む"""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


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

    # 設定ファイルの読み込み
    config = load_config(args.config)
    print(f"Loaded config from: {args.config}")

    # コマンドライン引数で上書き
    if args.total_iterations is not None:
        config["training"]["total_iterations"] = args.total_iterations
    if args.device is not None:
        config["device"] = args.device
    if args.seed is not None:
        config["seed"] = args.seed

    # デバイス
    device = get_device(config.get("device", "auto"))
    print(f"Using device: {device}")

    # シード設定
    if config.get("seed") is not None:
        torch.manual_seed(config["seed"])
        import numpy as np

        np.random.seed(config["seed"])
        print(f"Random seed: {config['seed']}")

    # 実験名の自動生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_name = f"ppo_curriculum_{timestamp}"
    print(f"Experiment: {experiment_name}")

    # カリキュラム学習の設定確認
    curriculum_enabled = config.get("curriculum", {}).get("enabled", False)

    if curriculum_enabled:
        print("\n" + "=" * 60)
        print("CURRICULUM LEARNING ENABLED")
        print("=" * 60)
        courses = config["curriculum"]["courses"]
        for i, course in enumerate(courses):
            print(f"  Level {i}: {course}")
        print(f"  Success Threshold: {config['curriculum']['success_threshold']}")
        print(f"  Degradation Threshold: {config['curriculum']['degradation_threshold']}")
        print(f"  Evaluation Window: {config['curriculum']['evaluation_window']}")
        print("=" * 60 + "\n")

    # 環境の作成（初期コース）
    render_mode = "human" if args.gui else None
    if args.gui:
        print("GUI visualization enabled")

    initial_course = (
        config["curriculum"]["courses"][0]
        if curriculum_enabled
        else config["env"]["course"]
    )

    env = MinicarEnv(
        course_file=initial_course,
        render_mode=render_mode,
        max_steps=config["env"]["max_steps"],
    )

    # カリキュラムマネージャーの作成
    curriculum = None
    if curriculum_enabled:
        curriculum = CurriculumManager(
            courses=config["curriculum"]["courses"],
            success_threshold=config["curriculum"]["success_threshold"],
            degradation_threshold=config["curriculum"]["degradation_threshold"],
            evaluation_window=config["curriculum"]["evaluation_window"],
            min_episodes_before_advance=config["curriculum"][
                "min_episodes_before_advance"
            ],
            allow_degradation=config["curriculum"]["allow_degradation"],
        )
        print(f"Created CurriculumManager: {curriculum}")

    # PPOの作成
    ppo_config = config["ppo"]
    network_config = config["network"]

    ppo = PPO(
        obs_dim=env.observation_space.shape[0],
        action_dim=env.action_space.shape[0],
        device=device,
        hidden_dims=tuple(network_config["hidden_dims"]),
        use_shared_network=network_config["use_shared_network"],
        learning_rate=ppo_config["learning_rate"],
        gamma=ppo_config["gamma"],
        gae_lambda=ppo_config["gae_lambda"],
        clip_range=ppo_config["clip_range"],
        entropy_coef=ppo_config["entropy_coef"],
        value_coef=ppo_config["value_coef"],
        max_grad_norm=ppo_config["max_grad_norm"],
    )

    # チェックポイントから再開
    if args.resume is not None:
        ppo.load(args.resume)
        print(f"Resumed from checkpoint: {args.resume}")

    # ロガーの作成
    logging_config = config["logging"]
    logger = create_logger(
        log_dir=logging_config["log_dir"],
        experiment_name=experiment_name,
        use_tensorboard=logging_config["use_tensorboard"],
        use_csv=logging_config["use_csv"],
    )

    # ハイパーパラメータをログ
    hparams = {
        "device": str(device),
        "curriculum_enabled": curriculum_enabled,
        **config,
    }
    logger.log_hyperparams(hparams)

    # Trainerの作成
    training_config = config["training"]
    checkpoint_config = config["checkpoint"]
    evaluation_config = config["evaluation"]

    trainer = PPOTrainer(
        env=env,
        ppo=ppo,
        logger=logger,
        n_steps=training_config["n_steps"],
        n_epochs=training_config["n_epochs"],
        batch_size=training_config["batch_size"],
        save_freq=checkpoint_config["save_freq"],
        checkpoint_dir=checkpoint_config["checkpoint_dir"],
        eval_freq=evaluation_config["eval_freq"],
        n_eval_episodes=evaluation_config["n_eval_episodes"],
        curriculum=curriculum,
    )

    # 学習開始
    print("\n" + "=" * 60)
    print("STARTING CURRICULUM LEARNING")
    print("=" * 60)
    print(f"Total Iterations: {training_config['total_iterations']}")
    print(f"Steps per Iteration: {training_config['n_steps']}")
    print(
        f"Total Timesteps: {training_config['total_iterations'] * training_config['n_steps']}"
    )
    print("=" * 60 + "\n")

    try:
        trainer.train(total_iterations=training_config["total_iterations"])
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user")
    finally:
        # カリキュラム統計を表示
        if curriculum is not None:
            print("\n" + "=" * 60)
            print("CURRICULUM LEARNING STATISTICS")
            print("=" * 60)
            stats = curriculum.get_stats()
            print(f"Final Level: {stats['current_level']}/{stats['total_courses']-1}")
            print(f"Final Course: {stats['current_course']}")
            print(f"Success Rate: {stats['success_rate']:.2%}")
            print(f"Total Episodes: {stats['total_episodes']}")
            print(f"Level Changes: {stats['level_changes']}")
            print("=" * 60 + "\n")

        # ログを保存して閉じる
        logger.save()
        logger.close()
        env.close()

    print("Training finished!")


if __name__ == "__main__":
    main()
