"""カリキュラム学習マネージャー

難易度の段階的調整を行い、効率的な学習を実現する。
"""

import numpy as np
from collections import deque
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CurriculumManager:
    """カリキュラム学習を管理するクラス

    成功率に基づいて自動的に難易度レベルを調整する。

    Attributes:
        courses: コースパスのリスト（易→難の順）
        current_level: 現在の難易度レベル（0始まり）
        success_threshold: レベルアップに必要な成功率
        degradation_threshold: レベルダウンする成功率
        recent_results: 最近のエピソード結果（成功/失敗）
        evaluation_window: 成功率評価のウィンドウサイズ
        min_episodes_before_advance: レベルアップまでの最小エピソード数
    """

    def __init__(
        self,
        courses: List[str],
        success_threshold: float = 0.8,
        degradation_threshold: float = 0.3,
        evaluation_window: int = 100,
        min_episodes_before_advance: int = 50,
        allow_degradation: bool = True,
        randomize_from_level: Optional[int] = None,
    ):
        """
        Args:
            courses: コースファイルパスのリスト（易→難の順）
            success_threshold: レベルアップに必要な成功率（0.0-1.0）
            degradation_threshold: レベルダウンする成功率（0.0-1.0）
            evaluation_window: 成功率を計算する直近エピソード数
            min_episodes_before_advance: レベルアップ判定の最小エピソード数
            allow_degradation: 難易度を下げることを許可するか
            randomize_from_level: このレベル以降でランダムにコースを選択（Noneで無効）
        """
        if not courses:
            raise ValueError("At least one course must be provided")

        if not (0.0 <= success_threshold <= 1.0):
            raise ValueError("success_threshold must be between 0.0 and 1.0")

        if not (0.0 <= degradation_threshold <= 1.0):
            raise ValueError("degradation_threshold must be between 0.0 and 1.0")

        if degradation_threshold >= success_threshold:
            raise ValueError(
                "degradation_threshold must be less than success_threshold"
            )

        # コースの存在確認
        for course_path in courses:
            if not Path(course_path).exists():
                logger.warning(f"Course file not found: {course_path}")

        self.courses = courses
        self.current_level = 0
        self.success_threshold = success_threshold
        self.degradation_threshold = degradation_threshold
        self.evaluation_window = evaluation_window
        self.min_episodes_before_advance = min_episodes_before_advance
        self.allow_degradation = allow_degradation
        self.randomize_from_level = randomize_from_level

        # 最近のエピソード結果を保存（True=成功, False=失敗）
        self.recent_results = deque(maxlen=evaluation_window)

        # 統計情報
        self.total_episodes = 0
        self.level_episodes = 0  # 現在のレベルでのエピソード数
        self.level_change_history = []  # レベル変更履歴

        logger.info(
            f"CurriculumManager initialized with {len(courses)} courses"
        )
        logger.info(f"Success threshold: {success_threshold}")
        logger.info(f"Degradation threshold: {degradation_threshold}")
        if randomize_from_level is not None:
            logger.info(f"Randomization enabled from level {randomize_from_level}")

    def update(self, success: bool) -> None:
        """エピソード結果を記録

        Args:
            success: エピソードが成功したか（True=成功, False=失敗）
        """
        self.recent_results.append(success)
        self.total_episodes += 1
        self.level_episodes += 1

    def get_current_course(self) -> str:
        """現在のコースパスを取得

        Returns:
            現在のレベルに対応するコースファイルパス
            randomize_from_level以降では、そのレベル以降のコースからランダムに選択
        """
        # ランダム化が有効で、指定レベル以降の場合
        if (self.randomize_from_level is not None and
            self.current_level >= self.randomize_from_level):
            # 指定レベル以降のコースからランダムに選択
            available_courses = self.courses[self.randomize_from_level:]
            return np.random.choice(available_courses)

        # 通常の固定選択
        return self.courses[self.current_level]

    def get_success_rate(self) -> float:
        """現在の成功率を取得

        Returns:
            直近evaluation_windowエピソードの成功率（0.0-1.0）
            エピソード数が不足している場合は0.0を返す
        """
        if len(self.recent_results) == 0:
            return 0.0
        return np.mean(self.recent_results)

    def should_advance(self) -> bool:
        """次のレベルに進むべきか判定

        Returns:
            True: 次のレベルに進むべき
            False: 現在のレベルを継続
        """
        # 最後のレベルの場合は進めない
        if self.current_level >= len(self.courses) - 1:
            return False

        # 最小エピソード数に達していない場合は進めない
        if self.level_episodes < self.min_episodes_before_advance:
            return False

        # 成功率が閾値を超えているか確認
        success_rate = self.get_success_rate()
        return success_rate >= self.success_threshold

    def should_degrade(self) -> bool:
        """前のレベルに戻るべきか判定

        Returns:
            True: 前のレベルに戻るべき
            False: 現在のレベルを継続
        """
        # degradationが無効な場合は戻らない
        if not self.allow_degradation:
            return False

        # 最初のレベルの場合は戻れない
        if self.current_level == 0:
            return False

        # 最小エピソード数に達していない場合は判定しない
        if self.level_episodes < self.min_episodes_before_advance:
            return False

        # 成功率が低すぎる場合は前のレベルに戻る
        success_rate = self.get_success_rate()
        return success_rate < self.degradation_threshold

    def advance_level(self) -> bool:
        """次のレベルに進む

        Returns:
            True: レベルアップに成功
            False: レベルアップできなかった（既に最高レベル）
        """
        if self.current_level >= len(self.courses) - 1:
            logger.warning("Already at the highest level")
            return False

        old_level = self.current_level
        self.current_level += 1
        self.recent_results.clear()
        self.level_episodes = 0

        # 履歴を記録
        self.level_change_history.append({
            'episode': self.total_episodes,
            'from_level': old_level,
            'to_level': self.current_level,
            'type': 'advance',
        })

        logger.info(
            f"Advanced to level {self.current_level} "
            f"(course: {self.get_current_course()}) "
            f"after {self.total_episodes} total episodes"
        )
        return True

    def degrade_level(self) -> bool:
        """前のレベルに戻る

        Returns:
            True: レベルダウンに成功
            False: レベルダウンできなかった（既に最低レベル）
        """
        if self.current_level == 0:
            logger.warning("Already at the lowest level")
            return False

        old_level = self.current_level
        self.current_level -= 1
        self.recent_results.clear()
        self.level_episodes = 0

        # 履歴を記録
        self.level_change_history.append({
            'episode': self.total_episodes,
            'from_level': old_level,
            'to_level': self.current_level,
            'type': 'degrade',
        })

        logger.warning(
            f"Degraded to level {self.current_level} "
            f"(course: {self.get_current_course()}) "
            f"due to low success rate"
        )
        return True

    def auto_adjust_level(self) -> Optional[str]:
        """自動的にレベルを調整

        should_advance()やshould_degrade()の結果に基づいて
        自動的にレベルを変更する。

        Returns:
            'advanced': レベルアップした
            'degraded': レベルダウンした
            None: レベル変更なし
        """
        if self.should_advance():
            if self.advance_level():
                return 'advanced'
        elif self.should_degrade():
            if self.degrade_level():
                return 'degraded'
        return None

    def get_stats(self) -> Dict:
        """統計情報を取得

        Returns:
            統計情報の辞書
        """
        return {
            'current_level': self.current_level,
            'current_course': self.get_current_course(),
            'total_courses': len(self.courses),
            'success_rate': self.get_success_rate(),
            'total_episodes': self.total_episodes,
            'level_episodes': self.level_episodes,
            'recent_results_count': len(self.recent_results),
            'level_changes': len(self.level_change_history),
        }

    def reset(self) -> None:
        """カリキュラムをリセット（最初のレベルに戻る）"""
        self.current_level = 0
        self.recent_results.clear()
        self.total_episodes = 0
        self.level_episodes = 0
        self.level_change_history.clear()
        logger.info("Curriculum reset to level 0")

    def __repr__(self) -> str:
        stats = self.get_stats()
        return (
            f"CurriculumManager(level={stats['current_level']}/{stats['total_courses']-1}, "
            f"success_rate={stats['success_rate']:.2%}, "
            f"episodes={stats['level_episodes']}/{stats['total_episodes']})"
        )
