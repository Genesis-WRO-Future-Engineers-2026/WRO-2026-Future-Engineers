"""個別の報酬成分の実装"""

import numpy as np
from .base import RewardComponent, RewardContext


class TimePenaltyReward(RewardComponent):
    """時間ペナルティ報酬

    早くゴールするインセンティブを与える。
    """

    def __init__(self, penalty_per_step: float = 0.7):
        """
        Args:
            penalty_per_step: 1ステップあたりのペナルティ
        """
        super().__init__(weight=1.0)
        self.penalty_per_step = penalty_per_step

    def compute(self, context: RewardContext) -> float:
        return -self.penalty_per_step


class DirectionReward(RewardComponent):
    """方向報酬（チェックポイント/ゴールへの誘導）

    次の目標地点（チェックポイントまたはゴール）への距離に基づいて報酬を与える。
    """

    def __init__(
        self,
        max_distance: float = 20.0,
        reward_scale: float = 0.7,
    ):
        """
        Args:
            max_distance: 距離の正規化に使う最大値（m）
            reward_scale: 報酬のスケール係数
        """
        super().__init__(weight=1.0)
        self.max_distance = max_distance
        self.reward_scale = reward_scale

    def compute(self, context: RewardContext) -> float:
        # 次のチェックポイントまたはゴールの位置を取得
        if context.next_checkpoint_index < len(context.checkpoints):
            target_pos = context.checkpoints[context.next_checkpoint_index]["position"]
        else:
            target_pos = context.goal_position

        # 目標までの距離
        distance = np.linalg.norm(
            np.array(context.position) - np.array(target_pos)
        )

        # 正規化（近いほど高報酬）
        normalized_distance = min(distance, self.max_distance)
        proximity = (self.max_distance - normalized_distance) / self.max_distance

        return proximity * self.reward_scale


class CheckpointReward(RewardComponent):
    """チェックポイント通過報酬

    注意: この報酬成分は副作用（next_checkpoint_indexの更新）を持つため、
    特別な扱いが必要。CompositeRewardで最後に計算されるべき。
    """

    def __init__(self, checkpoint_bonus: float = 200.0):
        """
        Args:
            checkpoint_bonus: チェックポイント通過時のボーナス
        """
        super().__init__(weight=1.0)
        self.checkpoint_bonus = checkpoint_bonus

    def compute(self, context: RewardContext) -> float:
        # この報酬成分は check_and_reward() で計算される
        return 0.0

    def check_and_reward(
        self,
        context: RewardContext,
        course,  # Courseオブジェクト
    ) -> tuple:
        """チェックポイント通過をチェックし、報酬と通過フラグを返す

        Args:
            context: 報酬コンテキスト
            course: Courseオブジェクト

        Returns:
            (reward, passed): 報酬値と通過フラグ
        """
        if context.next_checkpoint_index < len(context.checkpoints):
            if course.check_checkpoint(
                context.position,
                context.next_checkpoint_index
            ):
                return self.checkpoint_bonus, True

        return 0.0, False


class GoalReward(RewardComponent):
    """ゴール到達報酬

    全チェックポイントを通過してゴールに到達した場合の報酬。
    時間ボーナスも含む。
    """

    def __init__(
        self,
        goal_bonus: float = 500.0,
        time_bonus_scale: float = 2.0,
    ):
        """
        Args:
            goal_bonus: ゴール到達時の基本ボーナス
            time_bonus_scale: 時間ボーナスのスケール（remaining_steps * scale）
        """
        super().__init__(weight=1.0)
        self.goal_bonus = goal_bonus
        self.time_bonus_scale = time_bonus_scale

    def compute(self, context: RewardContext) -> float:
        # この報酬成分は check_and_reward() で計算される
        return 0.0

    def check_and_reward(
        self,
        context: RewardContext,
        course,  # Courseオブジェクト
    ) -> float:
        """ゴール到達をチェックし、報酬を返す

        Args:
            context: 報酬コンテキスト
            course: Courseオブジェクト

        Returns:
            報酬値
        """
        # 全チェックポイント通過済みか
        all_checkpoints_passed = (
            context.next_checkpoint_index == len(context.checkpoints)
        )

        # ゴール到達判定
        if all_checkpoints_passed and course.check_goal(context.position):
            # 基本ゴール報酬
            reward = self.goal_bonus

            # 時間ボーナス
            remaining_steps = context.max_steps - context.step_count
            time_bonus = remaining_steps * self.time_bonus_scale
            reward += time_bonus

            return reward

        return 0.0


class CollisionPenalty(RewardComponent):
    """衝突ペナルティ"""

    def __init__(self, penalty: float = -100.0):
        """
        Args:
            penalty: 衝突時のペナルティ（負の値）
        """
        super().__init__(weight=1.0)
        self.penalty = penalty

    def compute(self, context: RewardContext) -> float:
        if context.has_collision:
            return self.penalty
        return 0.0
