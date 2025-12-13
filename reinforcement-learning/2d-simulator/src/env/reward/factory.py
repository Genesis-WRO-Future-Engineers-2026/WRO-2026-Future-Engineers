"""報酬関数のファクトリー"""

from typing import Optional
from .composite import CompositeReward, AdaptiveCompositeReward
from .components import (
    TimePenaltyReward,
    DirectionReward,
    CheckpointReward,
    GoalReward,
    CollisionPenalty,
)


class RewardFactory:
    """報酬関数のファクトリークラス

    標準的な報酬関数の組み合わせを簡単に生成できる。
    """

    @staticmethod
    def create_default_reward(
        adaptive_scaler=None,
    ) -> CompositeReward:
        """デフォルトの報酬関数を作成

        Args:
            adaptive_scaler: 適応的報酬スケーラー（Noneの場合は固定係数）

        Returns:
            複合報酬関数
        """
        # 基本的な報酬成分
        components = [
            TimePenaltyReward(penalty_per_step=0.7),
            DirectionReward(max_distance=20.0, reward_scale=0.7),
            CollisionPenalty(penalty=-100.0),
        ]

        # チェックポイント報酬とゴール報酬
        checkpoint_reward = CheckpointReward(checkpoint_bonus=200.0)
        goal_reward = GoalReward(goal_bonus=500.0, time_bonus_scale=2.0)

        # 適応的スケーラーの有無で切り替え
        if adaptive_scaler is not None:
            reward_fn = AdaptiveCompositeReward(
                components=components,
                checkpoint_reward=checkpoint_reward,
                goal_reward=goal_reward,
                adaptive_scaler=adaptive_scaler,
            )
            # 初期係数を適用
            reward_fn.update_coefficients()
        else:
            reward_fn = CompositeReward(
                components=components,
                checkpoint_reward=checkpoint_reward,
                goal_reward=goal_reward,
            )

        return reward_fn

    @staticmethod
    def create_simple_reward() -> CompositeReward:
        """シンプルな報酬関数を作成（デバッグ用）

        Returns:
            複合報酬関数
        """
        # チェックポイント報酬とゴール報酬のみ
        checkpoint_reward = CheckpointReward(checkpoint_bonus=100.0)
        goal_reward = GoalReward(goal_bonus=100.0, time_bonus_scale=0.0)

        components = [
            CollisionPenalty(penalty=-10.0),
        ]

        return CompositeReward(
            components=components,
            checkpoint_reward=checkpoint_reward,
            goal_reward=goal_reward,
        )
