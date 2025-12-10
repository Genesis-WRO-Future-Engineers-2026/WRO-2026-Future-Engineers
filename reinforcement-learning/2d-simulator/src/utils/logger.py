"""TensorBoard統合とロギング"""

from torch.utils.tensorboard import SummaryWriter
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import json


class TensorBoardLogger:
    """TensorBoardロガー"""

    def __init__(
        self,
        log_dir: str = "logs",
        experiment_name: Optional[str] = None,
    ):
        """
        Args:
            log_dir: ログディレクトリ
            experiment_name: 実験名
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        if experiment_name is not None:
            self.log_dir = self.log_dir / experiment_name
            self.log_dir.mkdir(parents=True, exist_ok=True)

        self.writer = SummaryWriter(str(self.log_dir))
        print(f"TensorBoard log directory: {self.log_dir}")

    def log(self, data: Dict[str, Any], step: int):
        """
        データをログに記録

        Args:
            data: ログデータ（辞書）
            step: ステップ数
        """
        for key, value in data.items():
            if isinstance(value, (int, float, np.number)):
                self.writer.add_scalar(key, value, step)
            elif isinstance(value, np.ndarray):
                self.writer.add_histogram(key, value, step)

    def log_hyperparams(self, hparams: Dict[str, Any]):
        """
        ハイパーパラメータをログに記録

        Args:
            hparams: ハイパーパラメータ（辞書）
        """
        # TensorBoardに記録
        self.writer.add_hparams(
            hparams, {"hparam/dummy": 0}
        )  # dummy metricが必要

        # JSONファイルにも保存
        hparams_path = self.log_dir / "hyperparameters.json"
        with open(hparams_path, "w") as f:
            json.dump(hparams, f, indent=2)

        print(f"Hyperparameters saved to {hparams_path}")

    def log_text(self, tag: str, text: str, step: int):
        """
        テキストをログに記録

        Args:
            tag: タグ
            text: テキスト
            step: ステップ数
        """
        self.writer.add_text(tag, text, step)

    def log_image(self, tag: str, image: np.ndarray, step: int):
        """
        画像をログに記録

        Args:
            tag: タグ
            image: 画像（H x W x C または C x H x W）
            step: ステップ数
        """
        self.writer.add_image(tag, image, step, dataformats="HWC")

    def log_video(self, tag: str, video: np.ndarray, step: int, fps: int = 30):
        """
        動画をログに記録

        Args:
            tag: タグ
            video: 動画（T x H x W x C または T x C x H x W）
            step: ステップ数
            fps: フレームレート
        """
        self.writer.add_video(tag, video, step, fps=fps)

    def close(self):
        """ロガーを閉じる"""
        self.writer.close()


class CSVLogger:
    """CSV形式でログを保存"""

    def __init__(self, log_file: str = "logs/training.csv"):
        """
        Args:
            log_file: ログファイルのパス
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.data = []
        self.keys = set()

    def log(self, data: Dict[str, Any], step: int):
        """
        データをログに記録

        Args:
            data: ログデータ（辞書）
            step: ステップ数
        """
        # ステップを追加
        row = {"step": step}

        # データを追加
        for key, value in data.items():
            if isinstance(value, (int, float, np.number)):
                row[key] = value
                self.keys.add(key)

        self.data.append(row)

    def save(self):
        """CSVファイルに保存"""
        import csv

        if not self.data:
            return

        # すべてのキーを取得
        all_keys = ["step"] + sorted(self.keys)

        with open(self.log_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_keys)
            writer.writeheader()
            writer.writerows(self.data)

        print(f"CSV log saved to {self.log_file}")


class MultiLogger:
    """複数のロガーを統合"""

    def __init__(self, loggers: list):
        """
        Args:
            loggers: ロガーのリスト
        """
        self.loggers = loggers

    def log(self, data: Dict[str, Any], step: int):
        """
        データをすべてのロガーに記録

        Args:
            data: ログデータ（辞書）
            step: ステップ数
        """
        for logger in self.loggers:
            logger.log(data, step)

    def log_hyperparams(self, hparams: Dict[str, Any]):
        """
        ハイパーパラメータを記録

        Args:
            hparams: ハイパーパラメータ（辞書）
        """
        for logger in self.loggers:
            if hasattr(logger, "log_hyperparams"):
                logger.log_hyperparams(hparams)

    def close(self):
        """すべてのロガーを閉じる"""
        for logger in self.loggers:
            if hasattr(logger, "close"):
                logger.close()

    def save(self):
        """すべてのロガーを保存"""
        for logger in self.loggers:
            if hasattr(logger, "save"):
                logger.save()


def create_logger(
    log_dir: str = "logs",
    experiment_name: Optional[str] = None,
    use_tensorboard: bool = True,
    use_csv: bool = True,
) -> MultiLogger:
    """
    ロガーを作成

    Args:
        log_dir: ログディレクトリ
        experiment_name: 実験名
        use_tensorboard: TensorBoardを使うか
        use_csv: CSVを使うか

    Returns:
        マルチロガー
    """
    loggers = []

    if use_tensorboard:
        tb_logger = TensorBoardLogger(log_dir, experiment_name)
        loggers.append(tb_logger)

    if use_csv:
        csv_path = Path(log_dir)
        if experiment_name:
            csv_path = csv_path / experiment_name
        csv_path = csv_path / "training.csv"
        csv_logger = CSVLogger(str(csv_path))
        loggers.append(csv_logger)

    return MultiLogger(loggers)
