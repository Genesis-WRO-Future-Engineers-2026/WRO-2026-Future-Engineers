"""学習ループ（Trainer）"""

import torch
import numpy as np
from typing import Optional, Dict
import time
from pathlib import Path
import pygame

from src.rl.ppo import PPO
from src.rl.buffer import RolloutBuffer
from src.env.minicar_env import MinicarEnv
from src.curriculum.curriculum_manager import CurriculumManager


class PPOTrainer:
    """PPOの学習を管理するTrainer"""

    def __init__(
        self,
        env: MinicarEnv,
        ppo: PPO,
        logger=None,
        # 学習パラメータ
        n_steps: int = 2048,
        n_epochs: int = 10,
        batch_size: int = 64,
        reward_clip: float = 10.0,
        # チェックポイント
        save_freq: int = 10,
        checkpoint_dir: str = "models/checkpoints",
        # 評価
        eval_freq: int = 10,
        n_eval_episodes: int = 5,
        # カリキュラム学習
        curriculum: Optional[CurriculumManager] = None,
    ):
        """
        Args:
            env: 環境
            ppo: PPOアルゴリズム
            logger: ロガー
            n_steps: ステップ数（1回の更新あたり）
            n_epochs: エポック数
            batch_size: バッチサイズ
            reward_clip: 報酬のクリッピング範囲（勾配爆発防止）
            save_freq: 保存頻度（イテレーション単位）
            checkpoint_dir: チェックポイントディレクトリ
            eval_freq: 評価頻度（イテレーション単位）
            n_eval_episodes: 評価エピソード数
            curriculum: カリキュラム学習マネージャー（オプション）
        """
        self.env = env
        self.ppo = ppo
        self.logger = logger
        self.n_steps = n_steps
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.save_freq = save_freq
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.eval_freq = eval_freq
        self.n_eval_episodes = n_eval_episodes
        self.curriculum = curriculum

        # ロールアウトバッファ
        self.rollout_buffer = RolloutBuffer(
            buffer_size=n_steps,
            obs_dim=env.observation_space.shape[0],
            action_dim=env.action_space.shape[0],
            device=ppo.device,
            gamma=ppo.gamma,
            gae_lambda=ppo.gae_lambda,
            reward_clip=reward_clip,
        )

        # 統計
        self.iteration = 0
        self.total_timesteps = 0
        self.episode_rewards = []
        self.episode_lengths = []

        # GUI制御
        self.gui_enabled = (env.render_mode == "human")
        self.show_gui = self.gui_enabled  # 動的にON/OFF可能

    def collect_rollouts(self) -> Dict[str, float]:
        """
        ロールアウトを収集

        Returns:
            統計情報
        """
        self.rollout_buffer.reset()

        episode_rewards = []
        episode_lengths = []
        episode_reward = 0
        episode_length = 0

        obs, _ = self.env.reset()

        for step in range(self.n_steps):
            # GUIイベントチェック（'G'キーでトグル）
            if self.gui_enabled:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_g:
                            self.show_gui = not self.show_gui
                            status = "ON" if self.show_gui else "OFF"
                            print(f"\n[GUI] Display toggled: {status}\n")
                    elif event.type == pygame.QUIT:
                        # ウィンドウを閉じた場合はGUIを無効化（学習は継続）
                        self.show_gui = False
                        print("\n[GUI] Window closed, GUI disabled (training continues)\n")

            # 行動を取得
            action, log_prob, value = self.ppo.get_action(obs)

            # 環境でステップを実行
            next_obs, reward, terminated, truncated, info = self.env.step(
                action
            )
            done = terminated or truncated

            # レンダリング（GUIがONの場合のみ）
            if self.gui_enabled and self.show_gui:
                self.env.render()

            # バッファに追加
            self.rollout_buffer.add(
                obs=obs,
                action=action,
                reward=reward,
                value=value,
                log_prob=log_prob,
                done=done,
            )

            obs = next_obs
            episode_reward += reward
            episode_length += 1
            self.total_timesteps += 1

            if done:
                episode_rewards.append(episode_reward)
                episode_lengths.append(episode_length)

                # カリキュラム学習: 成功/失敗を記録
                if self.curriculum is not None:
                    # 成功判定（全チェックポイント通過してゴール到達）
                    total_checkpoints = info.get("total_checkpoints", 0)
                    success = (
                        terminated
                        and info.get("next_checkpoint_index", 0) == total_checkpoints
                        and info.get("min_distance", 0) > 0.1
                    )
                    self.curriculum.update(success)

                # リセット
                obs, _ = self.env.reset()
                episode_reward = 0
                episode_length = 0

        # 最後の価値を計算（GAE用）
        with torch.no_grad():
            _, _, last_value = self.ppo.get_action(obs)

        # アドバンテージとリターンを計算
        self.rollout_buffer.compute_returns_and_advantages(last_value)

        # 統計
        stats = {
            "rollout/ep_rew_mean": (
                np.mean(episode_rewards) if episode_rewards else 0
            ),
            "rollout/ep_len_mean": (
                np.mean(episode_lengths) if episode_lengths else 0
            ),
            "rollout/n_episodes": len(episode_rewards),
        }

        return stats

    def train(self, total_iterations: int):
        """
        学習を実行

        Args:
            total_iterations: 総イテレーション数
        """
        print("=" * 60)
        print("PPO Training Start")
        print("=" * 60)
        print(f"Total iterations: {total_iterations}")
        print(f"Steps per iteration: {self.n_steps}")
        print(f"Total timesteps: {total_iterations * self.n_steps}")
        print("=" * 60)

        start_time = time.time()

        for iteration in range(total_iterations):
            self.iteration = iteration
            iter_start_time = time.time()

            # ロールアウト収集
            rollout_stats = self.collect_rollouts()

            # PPO更新
            update_stats = self.ppo.update(
                self.rollout_buffer,
                n_epochs=self.n_epochs,
                batch_size=self.batch_size,
            )

            # 統計のマージ
            stats = {**rollout_stats, **update_stats}

            # 時間統計
            iter_time = time.time() - iter_start_time
            fps = self.n_steps / iter_time
            stats["time/fps"] = fps
            stats["time/iterations"] = iteration + 1
            stats["time/total_timesteps"] = self.total_timesteps

            # カリキュラム学習: レベル調整
            if self.curriculum is not None:
                level_change = self.curriculum.auto_adjust_level()
                if level_change is not None:
                    # コースを変更
                    new_course = self.curriculum.get_current_course()
                    self.env.load_course(new_course)

                    # レベル変更をログ
                    curriculum_stats = self.curriculum.get_stats()
                    print(f"\n{'='*60}")
                    print(f"CURRICULUM LEVEL CHANGED: {level_change.upper()}")
                    print(f"New Level: {curriculum_stats['current_level']}")
                    print(f"New Course: {curriculum_stats['current_course']}")
                    print(f"Success Rate: {curriculum_stats['success_rate']:.2%}")
                    print(f"{'='*60}\n")

                # カリキュラム統計をログ
                curriculum_stats = self.curriculum.get_stats()
                stats["curriculum/level"] = curriculum_stats['current_level']
                stats["curriculum/success_rate"] = curriculum_stats['success_rate']
                stats["curriculum/level_episodes"] = curriculum_stats['level_episodes']

            # ログ
            if self.logger is not None:
                self.logger.log(stats, step=self.total_timesteps)

            # コンソール出力
            if (iteration + 1) % 1 == 0:
                elapsed_time = time.time() - start_time
                print(f"\nIteration {iteration + 1}/{total_iterations}")
                print(f"  Timesteps: {self.total_timesteps}")
                print(
                    f"  Episode Reward (mean): {stats['rollout/ep_rew_mean']:.2f}"
                )
                print(
                    f"  Episode Length (mean): {stats['rollout/ep_len_mean']:.1f}"
                )
                print(f"  Policy Loss: {stats['loss/policy']:.4f}")
                print(f"  Value Loss: {stats['loss/value']:.4f}")
                print(f"  FPS: {fps:.0f}")
                print(f"  Elapsed Time: {elapsed_time:.1f}s")

            # チェックポイント保存
            if (iteration + 1) % self.save_freq == 0:
                checkpoint_path = (
                    self.checkpoint_dir
                    / f"checkpoint_{iteration + 1}.pth"
                )
                self.ppo.save(str(checkpoint_path))
                print(f"  Saved checkpoint: {checkpoint_path}")

            # 評価
            if (iteration + 1) % self.eval_freq == 0:
                eval_stats = self.evaluate()
                if self.logger is not None:
                    self.logger.log(eval_stats, step=self.total_timesteps)
                print(
                    f"  Eval Reward (mean): {eval_stats['eval/ep_rew_mean']:.2f}"
                )
                print(
                    f"  Eval Success Rate: {eval_stats['eval/success_rate']:.2%}"
                )

        # 最終チェックポイント
        final_path = self.checkpoint_dir / "final_model.pth"
        self.ppo.save(str(final_path))
        print(f"\nTraining completed! Final model saved to {final_path}")

    def evaluate(self) -> Dict[str, float]:
        """
        評価を実行

        Returns:
            評価統計
        """
        episode_rewards = []
        episode_lengths = []
        successes = []

        for _ in range(self.n_eval_episodes):
            obs, _ = self.env.reset()
            episode_reward = 0
            episode_length = 0
            done = False

            while not done:
                # GUIイベントチェック（'G'キーでトグル）
                if self.gui_enabled:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_g:
                                self.show_gui = not self.show_gui
                                status = "ON" if self.show_gui else "OFF"
                                print(f"\n[GUI] Display toggled: {status}\n")
                        elif event.type == pygame.QUIT:
                            self.show_gui = False
                            print("\n[GUI] Window closed, GUI disabled (evaluation continues)\n")

                # 決定的に行動を選択
                action, _, _ = self.ppo.get_action(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.env.step(
                    action
                )
                done = terminated or truncated

                # レンダリング（GUIがONの場合のみ）
                if self.gui_enabled and self.show_gui:
                    self.env.render()

                episode_reward += reward
                episode_length += 1

            episode_rewards.append(episode_reward)
            episode_lengths.append(episode_length)

            # 成功判定（全チェックポイント通過してゴール到達）
            total_checkpoints = info.get("total_checkpoints", 0)
            success = (
                terminated
                and info.get("next_checkpoint_index", 0) == total_checkpoints
                and info.get("min_distance", 0) > 0.1
            )
            successes.append(success)

        return {
            "eval/ep_rew_mean": np.mean(episode_rewards),
            "eval/ep_len_mean": np.mean(episode_lengths),
            "eval/success_rate": np.mean(successes),
        }

    def load_checkpoint(self, path: str):
        """
        チェックポイントを読み込み

        Args:
            path: チェックポイントのパス
        """
        self.ppo.load(path)
        print(f"Loaded checkpoint from {path}")
