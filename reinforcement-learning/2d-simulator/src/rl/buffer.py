"""経験バッファ（Rollout Buffer）"""

import numpy as np
import torch
from typing import Dict, Tuple, Generator


class RolloutBuffer:
    """PPO用のロールアウトバッファ（GAEを含む）"""

    def __init__(
        self,
        buffer_size: int,
        obs_dim: int,
        action_dim: int,
        device: torch.device = torch.device("cpu"),
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        reward_clip: float = 10.0,
    ):
        """
        Args:
            buffer_size: バッファサイズ（ステップ数）
            obs_dim: 観測次元数
            action_dim: 行動次元数
            device: PyTorchデバイス
            gamma: 割引率
            gae_lambda: GAEのλ
            reward_clip: 報酬のクリッピング範囲（勾配爆発防止）
        """
        self.buffer_size = buffer_size
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.device = device
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.reward_clip = reward_clip

        # バッファの初期化
        self.observations = np.zeros((buffer_size, obs_dim), dtype=np.float32)
        self.actions = np.zeros((buffer_size, action_dim), dtype=np.float32)
        self.rewards = np.zeros(buffer_size, dtype=np.float32)
        self.values = np.zeros(buffer_size, dtype=np.float32)
        self.log_probs = np.zeros(buffer_size, dtype=np.float32)
        self.dones = np.zeros(buffer_size, dtype=np.float32)

        # GAE用
        self.advantages = np.zeros(buffer_size, dtype=np.float32)
        self.returns = np.zeros(buffer_size, dtype=np.float32)

        # ポインタ
        self.pos = 0
        self.full = False

    def add(
        self,
        obs: np.ndarray,
        action: np.ndarray,
        reward: float,
        value: float,
        log_prob: float,
        done: bool,
    ):
        """
        経験を追加

        Args:
            obs: 観測
            action: 行動
            reward: 報酬
            value: 状態価値
            log_prob: 対数確率
            done: 終了フラグ
        """
        self.observations[self.pos] = np.array(obs).copy()
        self.actions[self.pos] = np.array(action).copy()
        self.rewards[self.pos] = reward
        self.values[self.pos] = value
        self.log_probs[self.pos] = log_prob
        self.dones[self.pos] = done

        self.pos += 1
        if self.pos == self.buffer_size:
            self.full = True
            self.pos = 0

    def compute_returns_and_advantages(self, last_value: float):
        """
        GAEを使ってアドバンテージとリターンを計算

        Args:
            last_value: 最後の状態の価値
        """
        # 報酬をクリッピング（勾配爆発防止）
        clipped_rewards = np.clip(
            self.rewards, -self.reward_clip, self.reward_clip
        )

        last_gae_lam = 0
        for step in reversed(range(self.buffer_size)):
            if step == self.buffer_size - 1:
                next_non_terminal = 1.0 - self.dones[step]
                next_value = last_value
            else:
                next_non_terminal = 1.0 - self.dones[step]
                next_value = self.values[step + 1]

            # TD誤差（クリッピングされた報酬を使用）
            delta = (
                clipped_rewards[step]
                + self.gamma * next_value * next_non_terminal
                - self.values[step]
            )

            # GAE
            self.advantages[step] = last_gae_lam = (
                delta
                + self.gamma
                * self.gae_lambda
                * next_non_terminal
                * last_gae_lam
            )

        # リターン = アドバンテージ + 価値
        self.returns = self.advantages + self.values

    def get(
        self, batch_size: int = None
    ) -> Generator[Dict[str, torch.Tensor], None, None]:
        """
        バッファからミニバッチを取得

        Args:
            batch_size: ミニバッチサイズ（Noneの場合は全データ）

        Yields:
            ミニバッチのデータ
        """
        indices = np.arange(self.buffer_size)
        np.random.shuffle(indices)

        if batch_size is None:
            batch_size = self.buffer_size

        start_idx = 0
        while start_idx < self.buffer_size:
            batch_indices = indices[start_idx : start_idx + batch_size]

            yield self._get_samples(batch_indices)

            start_idx += batch_size

    def _get_samples(
        self, batch_indices: np.ndarray
    ) -> Dict[str, torch.Tensor]:
        """
        指定されたインデックスのサンプルを取得

        Args:
            batch_indices: バッチのインデックス

        Returns:
            サンプルの辞書
        """
        data = {
            "observations": torch.as_tensor(
                self.observations[batch_indices], device=self.device
            ),
            "actions": torch.as_tensor(
                self.actions[batch_indices], device=self.device
            ),
            "values": torch.as_tensor(
                self.values[batch_indices], device=self.device
            ).unsqueeze(-1),
            "log_probs": torch.as_tensor(
                self.log_probs[batch_indices], device=self.device
            ),
            "advantages": torch.as_tensor(
                self.advantages[batch_indices], device=self.device
            ),
            "returns": torch.as_tensor(
                self.returns[batch_indices], device=self.device
            ).unsqueeze(-1),
        }
        return data

    def reset(self):
        """バッファをリセット"""
        self.pos = 0
        self.full = False

    def size(self) -> int:
        """現在のバッファサイズを返す"""
        if self.full:
            return self.buffer_size
        return self.pos


class SimpleBuffer:
    """シンプルな経験バッファ（GAE無し）"""

    def __init__(
        self,
        buffer_size: int,
        obs_dim: int,
        action_dim: int,
        device: torch.device = torch.device("cpu"),
    ):
        """
        Args:
            buffer_size: バッファサイズ
            obs_dim: 観測次元数
            action_dim: 行動次元数
            device: PyTorchデバイス
        """
        self.buffer_size = buffer_size
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.device = device

        # バッファの初期化
        self.observations = np.zeros((buffer_size, obs_dim), dtype=np.float32)
        self.actions = np.zeros((buffer_size, action_dim), dtype=np.float32)
        self.rewards = np.zeros(buffer_size, dtype=np.float32)
        self.next_observations = np.zeros(
            (buffer_size, obs_dim), dtype=np.float32
        )
        self.dones = np.zeros(buffer_size, dtype=np.float32)

        # ポインタ
        self.pos = 0
        self.full = False

    def add(
        self,
        obs: np.ndarray,
        action: np.ndarray,
        reward: float,
        next_obs: np.ndarray,
        done: bool,
    ):
        """
        経験を追加

        Args:
            obs: 観測
            action: 行動
            reward: 報酬
            next_obs: 次の観測
            done: 終了フラグ
        """
        self.observations[self.pos] = np.array(obs).copy()
        self.actions[self.pos] = np.array(action).copy()
        self.rewards[self.pos] = reward
        self.next_observations[self.pos] = np.array(next_obs).copy()
        self.dones[self.pos] = done

        self.pos += 1
        if self.pos == self.buffer_size:
            self.full = True
            self.pos = 0

    def sample(self, batch_size: int) -> Dict[str, torch.Tensor]:
        """
        ランダムにサンプリング

        Args:
            batch_size: バッチサイズ

        Returns:
            サンプルの辞書
        """
        max_idx = self.buffer_size if self.full else self.pos
        indices = np.random.randint(0, max_idx, size=batch_size)

        data = {
            "observations": torch.as_tensor(
                self.observations[indices], device=self.device
            ),
            "actions": torch.as_tensor(
                self.actions[indices], device=self.device
            ),
            "rewards": torch.as_tensor(
                self.rewards[indices], device=self.device
            ).unsqueeze(-1),
            "next_observations": torch.as_tensor(
                self.next_observations[indices], device=self.device
            ),
            "dones": torch.as_tensor(
                self.dones[indices], device=self.device
            ).unsqueeze(-1),
        }
        return data

    def reset(self):
        """バッファをリセット"""
        self.pos = 0
        self.full = False

    def size(self) -> int:
        """現在のバッファサイズを返す"""
        if self.full:
            return self.buffer_size
        return self.pos
