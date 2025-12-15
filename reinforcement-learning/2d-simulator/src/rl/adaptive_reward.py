"""適応的報酬スケーリング

学習の進捗に応じて報酬係数を自動調整し、常に適切なガイダンスを提供する。
"""

from typing import Dict, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class RewardCoefficients:
    """報酬係数のセット"""
    time_penalty: float
    direction_reward_scale: float
    checkpoint_reward: float
    goal_reward: float
    collision_penalty: float
    time_bonus_scale: float


class AdaptiveRewardScaler:
    """
    適応的報酬スケーリング

    学習の進捗（チェックポイント通過率、成功率）に応じて
    報酬係数を自動調整する。

    Phase 0（基礎走行）: 壁回避とチェックポイント発見を重視
    Phase 1（探索）: チェックポイント通過を重視
    Phase 2（最適化）: 速度最適化を重視
    """

    def __init__(
        self,
        initial_phase: int = 0,
        enable_auto_phase_transition: bool = True,
    ):
        """
        Args:
            initial_phase: 初期フェーズ（0: 基礎、1: 探索、2: 最適化）
            enable_auto_phase_transition: 自動フェーズ遷移を有効化
        """
        self.phase = initial_phase
        self.enable_auto_phase_transition = enable_auto_phase_transition

        # 各フェーズの報酬係数
        self.phase_coefficients = {
            0: RewardCoefficients(
                time_penalty=0.3,           # 弱め（まず動けるようにする）
                direction_reward_scale=1.2, # 強め（チェックポイントへ誘導）
                checkpoint_reward=150.0,    # やや控えめ
                goal_reward=500.0,
                collision_penalty=-100.0,
                time_bonus_scale=1.5,
            ),
            1: RewardCoefficients(
                time_penalty=0.5,           # 中程度
                direction_reward_scale=0.8, # やや弱め
                checkpoint_reward=200.0,    # 強め（通過を重視）
                goal_reward=500.0,
                collision_penalty=-100.0,
                time_bonus_scale=2.0,
            ),
            2: RewardCoefficients(
                time_penalty=0.7,           # 強め（速度最適化）
                direction_reward_scale=0.5, # 弱め（方向はもう学習済み）
                checkpoint_reward=200.0,
                goal_reward=500.0,
                collision_penalty=-100.0,
                time_bonus_scale=2.5,       # 強め（早いほど高報酬）
            ),
        }

        # 統計情報（フェーズ遷移判定用）
        self.recent_success_rate = 0.0
        self.recent_avg_checkpoints_passed = 0.0
        self.episodes_in_current_phase = 0

        # フェーズ遷移の閾値
        self.phase_transition_thresholds = {
            0: {  # Phase 0 → 1
                'min_success_rate': 0.3,
                'min_avg_checkpoints': 0.5,
                'min_episodes': 100,
            },
            1: {  # Phase 1 → 2
                'min_success_rate': 0.6,
                'min_avg_checkpoints': 0.8,
                'min_episodes': 100,
            },
        }

    def get_coefficients(self) -> RewardCoefficients:
        """
        現在のフェーズの報酬係数を取得

        Returns:
            報酬係数のセット
        """
        return self.phase_coefficients[self.phase]

    def update_statistics(
        self,
        success_rate: float,
        avg_checkpoints_passed: float,
    ):
        """
        統計情報を更新し、必要に応じてフェーズ遷移

        Args:
            success_rate: 最近の成功率（0.0 ~ 1.0）
            avg_checkpoints_passed: 最近の平均チェックポイント通過率（0.0 ~ 1.0）
        """
        self.recent_success_rate = success_rate
        self.recent_avg_checkpoints_passed = avg_checkpoints_passed
        self.episodes_in_current_phase += 1

        if self.enable_auto_phase_transition:
            self._check_phase_transition()

    def _check_phase_transition(self) -> Optional[int]:
        """
        フェーズ遷移条件をチェック

        Returns:
            新しいフェーズ（遷移しない場合はNone）
        """
        # Phase 2が最終フェーズ
        if self.phase >= 2:
            return None

        thresholds = self.phase_transition_thresholds.get(self.phase)
        if thresholds is None:
            return None

        # 条件チェック
        if (
            self.recent_success_rate >= thresholds['min_success_rate']
            and self.recent_avg_checkpoints_passed >= thresholds['min_avg_checkpoints']
            and self.episodes_in_current_phase >= thresholds['min_episodes']
        ):
            # フェーズ遷移
            old_phase = self.phase
            self.phase += 1
            self.episodes_in_current_phase = 0

            print(f"\n{'='*60}")
            print(f"REWARD PHASE TRANSITION: {old_phase} → {self.phase}")
            print(f"Success Rate: {self.recent_success_rate:.2%}")
            print(f"Avg CP Passed: {self.recent_avg_checkpoints_passed:.2%}")
            print(f"New Coefficients:")
            coeffs = self.get_coefficients()
            print(f"  time_penalty: {coeffs.time_penalty}")
            print(f"  direction_reward_scale: {coeffs.direction_reward_scale}")
            print(f"  checkpoint_reward: {coeffs.checkpoint_reward}")
            print(f"{'='*60}\n")

            return self.phase

        return None

    def get_phase_info(self) -> Dict[str, float]:
        """
        現在のフェーズ情報を取得

        Returns:
            フェーズ情報の辞書
        """
        return {
            'reward_phase': self.phase,
            'episodes_in_phase': self.episodes_in_current_phase,
            'success_rate': self.recent_success_rate,
            'avg_checkpoints_passed': self.recent_avg_checkpoints_passed,
        }

    def force_phase(self, phase: int):
        """
        フェーズを強制的に設定（デバッグ用）

        Args:
            phase: 新しいフェーズ（0, 1, 2）
        """
        if phase not in [0, 1, 2]:
            raise ValueError(f"Invalid phase: {phase}. Must be 0, 1, or 2.")

        self.phase = phase
        self.episodes_in_current_phase = 0
        print(f"[INFO] Reward phase forced to {phase}")
