"""複合報酬関数の実装"""

from typing import List, Optional
from .base import RewardComponent, RewardContext
from .components import CheckpointReward, GoalReward


class CompositeReward:
    """複数の報酬成分を組み合わせた報酬関数

    Strategy Patternを使用し、報酬成分を柔軟に組み合わせることができる。
    """

    def __init__(
        self,
        components: List[RewardComponent],
        checkpoint_reward: Optional[CheckpointReward] = None,
        goal_reward: Optional[GoalReward] = None,
    ):
        """
        Args:
            components: 基本的な報酬成分のリスト
            checkpoint_reward: チェックポイント報酬（副作用あり）
            goal_reward: ゴール報酬（副作用あり）
        """
        self.components = components
        self.checkpoint_reward = checkpoint_reward
        self.goal_reward = goal_reward

    def compute(
        self,
        context: RewardContext,
        course,  # Courseオブジェクト
    ) -> tuple:
        """報酬を計算

        Args:
            context: 報酬コンテキスト
            course: Courseオブジェクト

        Returns:
            (total_reward, checkpoint_passed): 総報酬とチェックポイント通過フラグ
        """
        total_reward = 0.0
        checkpoint_passed = False

        # 基本的な報酬成分を計算
        for component in self.components:
            total_reward += component(context)

        # チェックポイント報酬（副作用: next_checkpoint_indexの更新）
        if self.checkpoint_reward is not None:
            cp_reward, checkpoint_passed = self.checkpoint_reward.check_and_reward(
                context, course
            )
            total_reward += cp_reward

        # ゴール報酬
        if self.goal_reward is not None:
            goal_reward_value = self.goal_reward.check_and_reward(context, course)
            total_reward += goal_reward_value

        return total_reward, checkpoint_passed


class AdaptiveCompositeReward(CompositeReward):
    """適応的報酬スケーリング対応の複合報酬関数

    AdaptiveRewardScalerと連携し、学習の進捗に応じて
    報酬係数を自動調整する。
    """

    def __init__(
        self,
        components: List[RewardComponent],
        checkpoint_reward: Optional[CheckpointReward] = None,
        goal_reward: Optional[GoalReward] = None,
        adaptive_scaler=None,  # AdaptiveRewardScaler
    ):
        """
        Args:
            components: 基本的な報酬成分のリスト
            checkpoint_reward: チェックポイント報酬
            goal_reward: ゴール報酬
            adaptive_scaler: 適応的報酬スケーラー（Noneの場合は固定係数）
        """
        super().__init__(components, checkpoint_reward, goal_reward)
        self.adaptive_scaler = adaptive_scaler

    def update_coefficients(self):
        """適応的スケーラーから係数を取得し、各報酬成分を更新"""
        if self.adaptive_scaler is None:
            return

        coeffs = self.adaptive_scaler.get_coefficients()

        # 各報酬成分の係数を更新
        for component in self.components:
            component_name = type(component).__name__

            if component_name == "TimePenaltyReward":
                component.penalty_per_step = coeffs.time_penalty
            elif component_name == "DirectionReward":
                component.reward_scale = coeffs.direction_reward_scale
            elif component_name == "CollisionPenalty":
                component.penalty = coeffs.collision_penalty

        if self.checkpoint_reward is not None:
            self.checkpoint_reward.checkpoint_bonus = coeffs.checkpoint_reward

        if self.goal_reward is not None:
            self.goal_reward.goal_bonus = coeffs.goal_reward
            self.goal_reward.time_bonus_scale = coeffs.time_bonus_scale
