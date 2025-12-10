"""ポリシーネットワーク（Actor）"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Normal
import numpy as np
from typing import Tuple


class GaussianPolicy(nn.Module):
    """連続行動空間のためのGaussianポリシー"""

    def __init__(
        self,
        obs_dim: int = 77,
        action_dim: int = 2,
        hidden_dims: Tuple[int, ...] = (256, 256),
        log_std_min: float = -20.0,
        log_std_max: float = 2.0,
    ):
        """
        Args:
            obs_dim: 観測次元数
            action_dim: 行動次元数
            hidden_dims: 隠れ層のサイズ
            log_std_min: log(std)の最小値
            log_std_max: log(std)の最大値
        """
        super().__init__()

        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.log_std_min = log_std_min
        self.log_std_max = log_std_max

        # 観測の正規化
        self.obs_normalizer = nn.LayerNorm(obs_dim)

        # 共有エンコーダ
        layers = []
        prev_dim = obs_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.LayerNorm(hidden_dim))
            layers.append(nn.Tanh())
            prev_dim = hidden_dim

        self.encoder = nn.Sequential(*layers)

        # 平均（mean）と標準偏差（log_std）のヘッド
        self.mean_head = nn.Linear(prev_dim, action_dim)
        self.log_std_head = nn.Linear(prev_dim, action_dim)

        # 重みの初期化
        self._initialize_weights()

    def _initialize_weights(self):
        """重みの初期化"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)

        # 最終層は小さい値で初期化
        nn.init.orthogonal_(self.mean_head.weight, gain=0.01)
        nn.init.constant_(self.mean_head.bias, 0.0)
        nn.init.orthogonal_(self.log_std_head.weight, gain=0.01)
        nn.init.constant_(self.log_std_head.bias, 0.0)

    def forward(
        self, obs: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        順伝播

        Args:
            obs: 観測 (batch_size, obs_dim)

        Returns:
            mean: 行動の平均 (batch_size, action_dim)
            std: 行動の標準偏差 (batch_size, action_dim)
        """
        # 観測の正規化
        x = self.obs_normalizer(obs)

        # エンコーダ
        features = self.encoder(x)

        # 平均と標準偏差
        mean = self.mean_head(features)
        log_std = self.log_std_head(features)

        # log_stdをクリップ
        log_std = torch.clamp(log_std, self.log_std_min, self.log_std_max)
        std = torch.exp(log_std)

        return mean, std

    def get_action(
        self, obs: torch.Tensor, deterministic: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        行動をサンプリング

        Args:
            obs: 観測 (batch_size, obs_dim)
            deterministic: 決定的に行動を選択するか

        Returns:
            action: 行動 (batch_size, action_dim)
            log_prob: 対数確率 (batch_size,)
            mean: 行動の平均 (batch_size, action_dim)
        """
        mean, std = self.forward(obs)

        if deterministic:
            # 決定的な行動（平均値）
            action = mean
            # 対数確率は計算しない（使わないため）
            log_prob = torch.zeros(obs.shape[0], device=obs.device)
        else:
            # 確率的な行動
            dist = Normal(mean, std)
            action = dist.rsample()  # reparameterization trick
            log_prob = dist.log_prob(action).sum(dim=-1)

        # 行動の範囲制限
        action = self._squash_action(action)

        return action, log_prob, mean

    def _squash_action(self, action: torch.Tensor) -> torch.Tensor:
        """
        行動を適切な範囲に制限

        steering: [-1, 1]
        throttle: [0, 1]

        Args:
            action: 生の行動 (batch_size, action_dim)

        Returns:
            squashed_action: 制限された行動 (batch_size, action_dim)
        """
        # steering (index 0): tanh で [-1, 1]
        steering = torch.tanh(action[:, 0:1])

        # throttle (index 1): sigmoid で [0, 1]
        throttle = torch.sigmoid(action[:, 1:2])

        return torch.cat([steering, throttle], dim=-1)

    def evaluate_actions(
        self, obs: torch.Tensor, actions: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        与えられた行動の対数確率とエントロピーを計算

        Args:
            obs: 観測 (batch_size, obs_dim)
            actions: 行動 (batch_size, action_dim)

        Returns:
            log_prob: 対数確率 (batch_size,)
            entropy: エントロピー (batch_size,)
        """
        mean, std = self.forward(obs)
        dist = Normal(mean, std)

        # 逆変換が必要（squashを元に戻す）
        # steering: atanh
        # throttle: logit
        steering_raw = torch.atanh(
            torch.clamp(actions[:, 0:1], -0.999, 0.999)
        )
        throttle_raw = torch.log(
            actions[:, 1:2] / (1 - actions[:, 1:2] + 1e-8)
        )
        actions_raw = torch.cat([steering_raw, throttle_raw], dim=-1)

        log_prob = dist.log_prob(actions_raw).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)

        return log_prob, entropy

    def get_log_prob(
        self, obs: torch.Tensor, actions: torch.Tensor
    ) -> torch.Tensor:
        """
        与えられた行動の対数確率を計算

        Args:
            obs: 観測 (batch_size, obs_dim)
            actions: 行動 (batch_size, action_dim)

        Returns:
            log_prob: 対数確率 (batch_size,)
        """
        log_prob, _ = self.evaluate_actions(obs, actions)
        return log_prob


class DeterministicPolicy(nn.Module):
    """決定的ポリシー（評価用）"""

    def __init__(
        self,
        obs_dim: int = 77,
        action_dim: int = 2,
        hidden_dims: Tuple[int, ...] = (256, 256),
    ):
        """
        Args:
            obs_dim: 観測次元数
            action_dim: 行動次元数
            hidden_dims: 隠れ層のサイズ
        """
        super().__init__()

        self.obs_dim = obs_dim
        self.action_dim = action_dim

        # 観測の正規化
        self.obs_normalizer = nn.LayerNorm(obs_dim)

        # ネットワーク
        layers = []
        prev_dim = obs_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.LayerNorm(hidden_dim))
            layers.append(nn.Tanh())
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, action_dim))
        self.network = nn.Sequential(*layers)

        # 重みの初期化
        self._initialize_weights()

    def _initialize_weights(self):
        """重みの初期化"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        """
        順伝播

        Args:
            obs: 観測 (batch_size, obs_dim)

        Returns:
            action: 行動 (batch_size, action_dim)
        """
        x = self.obs_normalizer(obs)
        raw_action = self.network(x)

        # steering: tanh で [-1, 1]
        steering = torch.tanh(raw_action[:, 0:1])

        # throttle: sigmoid で [0, 1]
        throttle = torch.sigmoid(raw_action[:, 1:2])

        action = torch.cat([steering, throttle], dim=-1)
        return action
