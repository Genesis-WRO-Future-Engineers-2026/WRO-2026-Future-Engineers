"""実機ロボット用6分間連続走行スクリプト

本番競技会での使用を想定:
- 壁情報やコース定義は不要（LiDARセンサーのみで走行）
- 学習済みPPOモデルを使用して実機を制御
- 6分間連続で走行
- センサーデータから10次元観測空間を構築
- モーター制御コマンドを送信

シミュレーターとの違い:
- Box2D物理エンジンは使用しない
- 実機のLiDAR、IMU、エンコーダーから直接データ取得
- 実機のサーボ・ESCに直接コマンド送信
"""

import sys
import time
import argparse
from pathlib import Path
import signal

import torch
import numpy as np

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rl.ppo import PPO
from src.deploy.sensor_interface import RaspberryPiSensorInterface, MockSensorInterface
from src.deploy.motor_interface import RaspberryPiMotorInterface, MockMotorInterface
from src.deploy.observation_builder import ObservationBuilder


class RealRobotController:
    """実機ロボット制御クラス"""

    def __init__(
        self,
        model_path: str,
        sensor_interface,
        motor_interface,
        duration: int = 360,
        device: str = "cpu",
    ):
        """
        Args:
            model_path: 学習済みモデルのパス
            sensor_interface: センサーインターフェース
            motor_interface: モーターインターフェース
            duration: 走行時間（秒）
            device: PyTorchデバイス（Raspberry Piでは"cpu"を推奨）
        """
        self.sensor = sensor_interface
        self.motor = motor_interface
        self.duration = duration
        self.device = torch.device(device)

        # 観測空間構築
        self.obs_builder = ObservationBuilder(sensor=self.sensor)

        # モデルロード
        self._load_model(model_path)

        # 統計情報
        self.total_steps = 0
        self.start_time = None

        # シグナルハンドラー（Ctrl+Cで安全に停止）
        signal.signal(signal.SIGINT, self._signal_handler)

        print("=" * 60)
        print("実機ロボットコントローラー初期化完了")
        print("=" * 60)

    def _load_model(self, model_path: str):
        """学習済みモデルをロード"""
        print(f"Loading model from {model_path}...")

        # PPOエージェント作成（観測空間: 10次元、行動空間: 2次元）
        obs_dim = 10
        action_dim = 2

        self.agent = PPO(
            obs_dim=obs_dim,
            action_dim=action_dim,
            hidden_dim=64,
            learning_rate=3e-4,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            entropy_coef=0.01,
            device=self.device,
        )

        # チェックポイントロード
        checkpoint = torch.load(model_path, map_location=self.device)
        self.agent.policy.load_state_dict(checkpoint["policy_state_dict"])
        self.agent.policy.eval()

        print("Model loaded successfully!")
        print(f"  Observation space: {obs_dim}次元")
        print(f"  Action space: {action_dim}次元")
        print(f"  Device: {self.device}")

    def run(self):
        """6分間連続走行を実行"""
        print("\n" + "=" * 60)
        print("走行開始！")
        print(f"Duration: {self.duration}秒")
        print("=" * 60)

        # センサーとモーターをリセット
        self.sensor.reset()
        self.motor.reset()
        self.obs_builder.reset()

        self.start_time = time.time()
        last_log_time = self.start_time

        try:
            while time.time() - self.start_time < self.duration:
                # 観測取得
                observation = self.obs_builder.build_observation()

                # 行動選択（決定論的推論）
                with torch.no_grad():
                    obs_tensor = torch.FloatTensor(observation).unsqueeze(0).to(self.device)
                    action, _ = self.agent.policy.get_action(obs_tensor, deterministic=True)
                    action = action.cpu().numpy()[0]

                # モーター制御
                steering, throttle = action[0], action[1]
                self.motor.set_control(steering, throttle)

                # 前回の行動を更新
                self.obs_builder.update_prev_action(action)

                self.total_steps += 1

                # ログ出力（10秒ごと）
                current_time = time.time()
                if current_time - last_log_time >= 10.0:
                    elapsed = current_time - self.start_time
                    remaining = self.duration - elapsed
                    print(f"  経過: {elapsed:.0f}秒 / 残り: {remaining:.0f}秒 / Steps: {self.total_steps}")
                    last_log_time = current_time

                # 制御周期（50Hz = 20ms）
                time.sleep(0.02)

        except KeyboardInterrupt:
            print("\n\nCtrl+C検出 - 走行を中断します")

        finally:
            self._cleanup()

    def _cleanup(self):
        """クリーンアップ処理"""
        print("\n" + "=" * 60)
        print("走行終了 - クリーンアップ中...")
        print("=" * 60)

        # モーター停止
        self.motor.stop()

        # 統計情報出力
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"総走行時間: {elapsed:.1f}秒")
            print(f"総ステップ数: {self.total_steps}")
            if self.total_steps > 0:
                print(f"平均制御周波数: {self.total_steps / elapsed:.1f} Hz")

        # センサーとモーターをクローズ
        self.sensor.close()
        self.motor.close()

        print("クリーンアップ完了")
        print("=" * 60)

    def _signal_handler(self, sig, frame):
        """シグナルハンドラー（Ctrl+C対応）"""
        print("\n\nシグナル受信 - 緊急停止します")
        self.motor.stop()
        self.sensor.close()
        self.motor.close()
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="実機ロボット用6分間連続走行（本番環境）"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="学習済みモデルのパス（例: models/checkpoints/final_model.pth）",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=360,
        help="走行時間（秒）デフォルト: 360（6分）",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="モックセンサー/モーターを使用（テストモード）",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="PyTorchデバイス（cpu/cuda/mps）デフォルト: cpu",
    )
    parser.add_argument(
        "--lidar-port",
        type=str,
        default="/dev/ttyUSB0",
        help="LiDARデバイスのポート",
    )
    parser.add_argument(
        "--steering-pin",
        type=int,
        default=17,
        help="ステアリングサーボのGPIOピン番号",
    )
    parser.add_argument(
        "--throttle-pin",
        type=int,
        default=18,
        help="スロットルESCのGPIOピン番号",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("実機ロボット6分間連続走行")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"Duration: {args.duration}秒")
    print(f"Mode: {'Mock (Test)' if args.mock else 'Real Hardware'}")
    print(f"Device: {args.device}")
    print("=" * 60)

    # センサーとモーターのインターフェース作成
    if args.mock:
        # テストモード（モックインターフェース）
        sensor = MockSensorInterface()
        motor = MockMotorInterface()
    else:
        # 実機モード
        sensor = RaspberryPiSensorInterface(lidar_port=args.lidar_port)
        motor = RaspberryPiMotorInterface(
            steering_pin=args.steering_pin,
            throttle_pin=args.throttle_pin,
        )

    # コントローラー作成と実行
    controller = RealRobotController(
        model_path=args.model,
        sensor_interface=sensor,
        motor_interface=motor,
        duration=args.duration,
        device=args.device,
    )

    controller.run()


if __name__ == "__main__":
    main()
