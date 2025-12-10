"""価値関数ネットワーク（Critic）"""

import torch
import torch.nn as nn
import numpy as np
from typing import Tuple


class ValueNetwork(nn.Module):
    """状態価値関数 V(s)"""

    def __init__(
        self,
        obs_dim: int = 77,
        hidden_dims: Tuple[int, ...] = (256, 256),
    ):
        """
        Args:
            obs_dim: 観測次元数
            hidden_dims: 隠れ層のサイズ
        """
        super().__init__()

        self.obs_dim = obs_dim

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

        # 価値の出力層
        layers.append(nn.Linear(prev_dim, 1))

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
            value: 状態価値 (batch_size, 1)
        """
        x = self.obs_normalizer(obs)
        value = self.network(x)
        return value


class QNetwork(nn.Module):
    """行動価値関数 Q(s, a)（オプション）"""

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

        # ネットワーク（観測と行動を連結）
        layers = []
        prev_dim = obs_dim + action_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.LayerNorm(hidden_dim))
            layers.append(nn.Tanh())
            prev_dim = hidden_dim

        # Q値の出力層
        layers.append(nn.Linear(prev_dim, 1))

        self.network = nn.Sequential(*layers)

        # 重みの初期化
        self._initialize_weights()

    def _initialize_weights(self):
        """重みの初期化"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0.0)

    def forward(
        self, obs: torch.Tensor, action: torch.Tensor
    ) -> torch.Tensor:
        """
        順伝播

        Args:
            obs: 観測 (batch_size, obs_dim)
            action: 行動 (batch_size, action_dim)

        Returns:
            q_value: Q値 (batch_size, 1)
        """
        obs_normalized = self.obs_normalizer(obs)
        x = torch.cat([obs_normalized, action], dim=-1)
        q_value = self.network(x)
        return q_value


class ActorCriticNetwork(nn.Module):
    """Actor-Criticの統合ネットワーク（共有エンコーダ版）"""

    def __init__(
        self,
        obs_dim: int = 77,
        action_dim: int = 2,
        shared_dims: Tuple[int, ...] = (256,),
        actor_dims: Tuple[int, ...] = (256,),
        critic_dims: Tuple[int, ...] = (256,),
        log_std_min: float = -20.0,
        log_std_max: float = 2.0,
    ):
        """
        Args:
            obs_dim: 観測次元数
            action_dim: 行動次元数
            shared_dims: 共有エンコーダの層サイズ
            actor_dims: Actorヘッドの層サイズ
            critic_dims: Criticヘッドの層サイズ
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
        shared_layers = []
        prev_dim = obs_dim
        for hidden_dim in shared_dims:
            shared_layers.append(nn.Linear(prev_dim, hidden_dim))
            shared_layers.append(nn.LayerNorm(hidden_dim))
            shared_layers.append(nn.Tanh())
            prev_dim = hidden_dim

        self.shared_encoder = nn.Sequential(*shared_layers)
        shared_out_dim = prev_dim

        # Actorヘッド
        actor_layers = []
        prev_dim = shared_out_dim
        for hidden_dim in actor_dims:
            actor_layers.append(nn.Linear(prev_dim, hidden_dim))
            actor_layers.append(nn.LayerNorm(hidden_dim))
            actor_layers.append(nn.Tanh())
            prev_dim = hidden_dim

        self.actor_encoder = nn.Sequential(*actor_layers)
        self.mean_head = nn.Linear(prev_dim, action_dim)
        self.log_std_head = nn.Linear(prev_dim, action_dim)

        # Criticヘッド
        critic_layers = []
        prev_dim = shared_out_dim
        for hidden_dim in critic_dims:
            critic_layers.append(nn.Linear(prev_dim, hidden_dim))
            critic_layers.append(nn.LayerNorm(hidden_dim))
            critic_layers.append(nn.Tanh())
            prev_dim = hidden_dim

        self.critic_encoder = nn.Sequential(*critic_layers)
        self.value_head = nn.Linear(prev_dim, 1)

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
        nn.init.orthogonal_(self.value_head.weight, gain=1.0)
        nn.init.constant_(self.value_head.bias, 0.0)

    def forward(
        self, obs: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        順伝播

        Args:
            obs: 観測 (batch_size, obs_dim)

        Returns:
            mean: 行動の平均 (batch_size, action_dim)
            std: 行動の標準偏差 (batch_size, action_dim)
            value: 状態価値 (batch_size, 1)
        """
        # 観測の正規化と共有エンコーダ
        x = self.obs_normalizer(obs)
        shared_features = self.shared_encoder(x)

        # Actor
        actor_features = self.actor_encoder(shared_features)
        mean = self.mean_head(actor_features)
        log_std = self.log_std_head(actor_features)
        log_std = torch.clamp(log_std, self.log_std_min, self.log_std_max)
        std = torch.exp(log_std)

        # Critic
        critic_features = self.critic_encoder(shared_features)
        value = self.value_head(critic_features)

        return mean, std, value

    def get_value(self, obs: torch.Tensor) -> torch.Tensor:
        """
        状態価値を取得

        Args:
            obs: 観測 (batch_size, obs_dim)

        Returns:
            value: 状態価値 (batch_size, 1)
        """
        _, _, value = self.forward(obs)
        return value

    def get_action_and_value(
        self, obs: torch.Tensor, deterministic: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        行動と状態価値を同時に取得

        Args:
            obs: 観測 (batch_size, obs_dim)
            deterministic: 決定的に行動を選択するか

        Returns:
            action: 行動 (batch_size, action_dim)
            log_prob: 対数確率 (batch_size,)
            value: 状態価値 (batch_size, 1)
            mean: 行動の平均 (batch_size, action_dim)
        """
        from torch.distributions import Normal

        mean, std, value = self.forward(obs)

        if deterministic:
            action = mean
            log_prob = torch.zeros(obs.shape[0], device=obs.device)
        else:
            dist = Normal(mean, std)
            action = dist.rsample()
            log_prob = dist.log_prob(action).sum(dim=-1)

        # 行動の範囲制限
        steering = torch.tanh(action[:, 0:1])
        throttle = torch.sigmoid(action[:, 1:2])
        action = torch.cat([steering, throttle], dim=-1)

        return action, log_prob, value, mean
