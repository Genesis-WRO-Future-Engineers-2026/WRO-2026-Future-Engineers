"""報酬関数モジュール

このモジュールは報酬計算の責務を分離し、
柔軟な報酬関数の組み合わせを可能にします。
"""

from .base import RewardComponent, RewardContext
from .components import (
    TimePenaltyReward,
    DirectionReward,
    CheckpointReward,
    GoalReward,
    CollisionPenalty,
)
from .composite import CompositeReward, AdaptiveCompositeReward
from .factory import RewardFactory

__all__ = [
    # 基底クラス
    "RewardComponent",
    "RewardContext",
    # 報酬成分
    "TimePenaltyReward",
    "DirectionReward",
    "CheckpointReward",
    "GoalReward",
    "CollisionPenalty",
    # 複合報酬
    "CompositeReward",
    "AdaptiveCompositeReward",
    # ファクトリー
    "RewardFactory",
]
