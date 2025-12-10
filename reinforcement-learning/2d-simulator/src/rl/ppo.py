"""PPO (Proximal Policy Optimization) アルゴリズム"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Normal
import numpy as np
from typing import Dict, Optional, Tuple

from src.rl.policy import GaussianPolicy
from src.rl.value import ValueNetwork, ActorCriticNetwork
from src.rl.buffer import RolloutBuffer


class PPO:
    """PPOアルゴリズム"""

    def __init__(
        self,
        obs_dim: int = 77,
        action_dim: int = 2,
        device: torch.device = torch.device("cpu"),
        # ネットワーク設定
        hidden_dims: Tuple[int, ...] = (256, 256),
        use_shared_network: bool = False,
        # PPOパラメータ
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_range: float = 0.2,
        clip_range_vf: Optional[float] = None,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
        max_grad_norm: float = 0.5,
        target_kl: Optional[float] = None,
        # 正規化
        normalize_advantage: bool = True,
    ):
        """
        Args:
            obs_dim: 観測次元数
            action_dim: 行動次元数
            device: PyTorchデバイス
            hidden_dims: 隠れ層のサイズ
            use_shared_network: Actor-Criticで共有ネットワークを使うか
            learning_rate: 学習率
            gamma: 割引率
            gae_lambda: GAEのλ
            clip_range: PPOのクリッピング範囲
            clip_range_vf: 価値関数のクリッピング範囲
            entropy_coef: エントロピーボーナスの係数
            value_coef: 価値関数損失の係数
            max_grad_norm: 勾配クリッピングの最大値
            target_kl: KLダイバージェンスの目標値（早期停止用）
            normalize_advantage: アドバンテージを正規化するか
        """
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.device = device
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_range = clip_range
        self.clip_range_vf = clip_range_vf
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef
        self.max_grad_norm = max_grad_norm
        self.target_kl = target_kl
        self.normalize_advantage = normalize_advantage

        # ネットワークの作成
        self.use_shared_network = use_shared_network

        if use_shared_network:
            # 共有ネットワーク
            self.actor_critic = ActorCriticNetwork(
                obs_dim=obs_dim,
                action_dim=action_dim,
                shared_dims=(256,),
                actor_dims=(256,),
                critic_dims=(256,),
            ).to(device)
            self.optimizer = optim.Adam(
                self.actor_critic.parameters(), lr=learning_rate
            )
        else:
            # 別々のネットワーク
            self.policy = GaussianPolicy(
                obs_dim=obs_dim,
                action_dim=action_dim,
                hidden_dims=hidden_dims,
            ).to(device)

            self.value_net = ValueNetwork(
                obs_dim=obs_dim,
                hidden_dims=hidden_dims,
            ).to(device)

            # 別々のオプティマイザ
            self.optimizer = optim.Adam(
                list(self.policy.parameters())
                + list(self.value_net.parameters()),
                lr=learning_rate,
            )

        # 統計
        self.n_updates = 0

    def get_action(
        self, obs: np.ndarray, deterministic: bool = False
    ) -> Tuple[np.ndarray, float, float]:
        """
        行動を取得

        Args:
            obs: 観測
            deterministic: 決定的に行動を選択するか

        Returns:
            action: 行動
            log_prob: 対数確率
            value: 状態価値
        """
        with torch.no_grad():
            obs_tensor = torch.as_tensor(
                obs, dtype=torch.float32, device=self.device
            ).unsqueeze(0)

            if self.use_shared_network:
                action, log_prob, value, _ = (
                    self.actor_critic.get_action_and_value(
                        obs_tensor, deterministic
                    )
                )
            else:
                action, log_prob, _ = self.policy.get_action(
                    obs_tensor, deterministic
                )
                value = self.value_net(obs_tensor)

            action = action.cpu().numpy()[0]
            log_prob = log_prob.cpu().item()
            value = value.cpu().item()

        return action, log_prob, value

    def update(
        self,
        rollout_buffer: RolloutBuffer,
        n_epochs: int = 10,
        batch_size: int = 64,
    ) -> Dict[str, float]:
        """
        PPO更新を実行

        Args:
            rollout_buffer: ロールアウトバッファ
            n_epochs: エポック数
            batch_size: バッチサイズ

        Returns:
            ログ情報
        """
        # 統計の初期化
        policy_losses = []
        value_losses = []
        entropy_losses = []
        clip_fractions = []
        kl_divs = []
        approx_kl_divs = []

        # 複数エポック
        for epoch in range(n_epochs):
            # ミニバッチで学習
            for batch in rollout_buffer.get(batch_size):
                # バッチデータ
                observations = batch["observations"]
                actions = batch["actions"]
                old_values = batch["values"]
                old_log_probs = batch["log_probs"]
                advantages = batch["advantages"]
                returns = batch["returns"]

                # アドバンテージの正規化
                if self.normalize_advantage:
                    advantages = (advantages - advantages.mean()) / (
                        advantages.std() + 1e-8
                    )

                # 現在のポリシーで評価
                if self.use_shared_network:
                    mean, std, values = self.actor_critic(observations)
                    dist = Normal(mean, std)

                    # 行動の逆変換（squashを元に戻す）
                    steering_raw = torch.atanh(
                        torch.clamp(actions[:, 0:1], -0.999, 0.999)
                    )
                    throttle_raw = torch.log(
                        actions[:, 1:2] / (1 - actions[:, 1:2] + 1e-8)
                    )
                    actions_raw = torch.cat([steering_raw, throttle_raw], dim=-1)

                    log_probs = dist.log_prob(actions_raw).sum(dim=-1)
                    entropy = dist.entropy().sum(dim=-1)
                else:
                    log_probs, entropy = self.policy.evaluate_actions(
                        observations, actions
                    )
                    values = self.value_net(observations)

                # 重要度サンプリング比
                ratio = torch.exp(log_probs - old_log_probs)

                # ポリシー損失（クリッピング）
                policy_loss_1 = advantages * ratio
                policy_loss_2 = advantages * torch.clamp(
                    ratio, 1 - self.clip_range, 1 + self.clip_range
                )
                policy_loss = -torch.min(policy_loss_1, policy_loss_2).mean()

                # 価値関数損失
                if self.clip_range_vf is not None:
                    # 価値関数もクリッピング
                    values_clipped = old_values + torch.clamp(
                        values - old_values,
                        -self.clip_range_vf,
                        self.clip_range_vf,
                    )
                    value_loss_1 = (values - returns).pow(2)
                    value_loss_2 = (values_clipped - returns).pow(2)
                    value_loss = torch.max(value_loss_1, value_loss_2).mean()
                else:
                    value_loss = (values - returns).pow(2).mean()

                # エントロピーボーナス
                entropy_loss = -entropy.mean()

                # 総損失
                loss = (
                    policy_loss
                    + self.value_coef * value_loss
                    + self.entropy_coef * entropy_loss
                )

                # 勾配更新
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(
                    self.parameters(), self.max_grad_norm
                )
                self.optimizer.step()

                # 統計
                policy_losses.append(policy_loss.item())
                value_losses.append(value_loss.item())
                entropy_losses.append(entropy_loss.item())

                # クリップされた割合
                clip_fraction = (
                    torch.abs(ratio - 1.0) > self.clip_range
                ).float().mean()
                clip_fractions.append(clip_fraction.item())

                # KLダイバージェンス（近似）
                with torch.no_grad():
                    log_ratio = log_probs - old_log_probs
                    approx_kl = ((ratio - 1) - log_ratio).mean()
                    approx_kl_divs.append(approx_kl.item())

            # 早期停止（KLダイバージェンスが大きすぎる場合）
            if self.target_kl is not None:
                if np.mean(approx_kl_divs) > 1.5 * self.target_kl:
                    print(
                        f"Early stopping at epoch {epoch} due to reaching max kl"
                    )
                    break

        self.n_updates += 1

        # ログ
        return {
            "loss/policy": np.mean(policy_losses),
            "loss/value": np.mean(value_losses),
            "loss/entropy": np.mean(entropy_losses),
            "train/clip_fraction": np.mean(clip_fractions),
            "train/approx_kl": np.mean(approx_kl_divs),
            "train/n_updates": self.n_updates,
        }

    def parameters(self):
        """パラメータを返す"""
        if self.use_shared_network:
            return self.actor_critic.parameters()
        else:
            return list(self.policy.parameters()) + list(
                self.value_net.parameters()
            )

    def save(self, path: str):
        """モデルを保存"""
        if self.use_shared_network:
            torch.save(
                {
                    "actor_critic": self.actor_critic.state_dict(),
                    "optimizer": self.optimizer.state_dict(),
                    "n_updates": self.n_updates,
                },
                path,
            )
        else:
            torch.save(
                {
                    "policy": self.policy.state_dict(),
                    "value_net": self.value_net.state_dict(),
                    "optimizer": self.optimizer.state_dict(),
                    "n_updates": self.n_updates,
                },
                path,
            )

    def load(self, path: str):
        """モデルを読み込み"""
        checkpoint = torch.load(path, map_location=self.device)

        if self.use_shared_network:
            self.actor_critic.load_state_dict(checkpoint["actor_critic"])
        else:
            self.policy.load_state_dict(checkpoint["policy"])
            self.value_net.load_state_dict(checkpoint["value_net"])

        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.n_updates = checkpoint.get("n_updates", 0)
