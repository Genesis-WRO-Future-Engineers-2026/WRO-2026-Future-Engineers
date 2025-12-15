"""終了条件の判定"""

from typing import Dict


class TerminationChecker:
    """終了条件のチェックを担当するクラス

    学習モードと本番モードで異なる終了条件を適用する。
    """

    def __init__(self, deployment_mode: bool = False):
        """
        Args:
            deployment_mode: 本番環境モード
                - False（学習モード）: ゴール到達・衝突で終了
                - True（本番モード）: 衝突のみ終了、ゴール到達は継続
        """
        self.deployment_mode = deployment_mode

    def check(
        self,
        vehicle_position: tuple,
        has_collision: bool,
        next_checkpoint_index: int,
        total_checkpoints: int,
        course,  # Courseオブジェクト
    ) -> tuple:
        """終了条件をチェック

        Args:
            vehicle_position: 車両位置
            has_collision: 衝突フラグ
            next_checkpoint_index: 次のチェックポイントインデックス
            total_checkpoints: 総チェックポイント数
            course: Courseオブジェクト

        Returns:
            (terminated, is_collision): 終了フラグと衝突フラグ
        """
        # 本番環境モード: 衝突のみ終了判定
        if self.deployment_mode:
            if has_collision:
                return True, True
            return False, False

        # 学習モード: ゴール到達で終了
        all_checkpoints_passed = (next_checkpoint_index == total_checkpoints)
        if all_checkpoints_passed and course.check_goal(vehicle_position):
            return True, False

        # 壁衝突
        if has_collision:
            return True, True

        return False, False
