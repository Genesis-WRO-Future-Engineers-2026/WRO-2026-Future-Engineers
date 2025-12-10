"""ステアリング0で回転する問題のデバッグスクリプト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from src.env.minicar_env import MinicarEnv


def main():
    """デバッグテスト"""
    print("=" * 60)
    print("回転問題のデバッグテスト")
    print("=" * 60)
    print()

    # 環境作成
    env = MinicarEnv(course_file="courses/easy/simple_oval.json", render_mode=None)

    # リセット
    obs, info = env.reset()
    print(f"初期状態:")
    print(f"  Position: ({obs[0]:.4f}, {obs[1]:.4f})")
    print(f"  Angle: {obs[2]:.4f} rad")
    print()

    # まず、車両の内部状態を直接確認
    vehicle_state = env.vehicle.get_state()
    print(f"車両の内部状態:")
    print(f"  Position: {vehicle_state['position']}")
    print(f"  Angle: {vehicle_state['angle']:.6f} rad")
    print(f"  Angular velocity: {vehicle_state['angular_velocity']:.6f} rad/s")
    print(f"  Velocity: {vehicle_state['velocity']}")
    print()

    # ステアリング=0、スロットル=0.5で50ステップ実行
    print("【前進テスト】ステアリング=0.0、スロットル=0.5で50ステップ実行:")
    print("-" * 60)

    for step in range(50):
        action = np.array([0.0, 0.5])  # ステアリング=0、スロットル=0.5

        obs, reward, terminated, truncated, info = env.step(action)

        # 車両の内部状態を取得
        vehicle_state = env.vehicle.get_state()

        if step < 5 or step % 20 == 0:
            print(f"[Step {step+1:3d}] Angle: {vehicle_state['angle']:.6f} rad ({vehicle_state['angle']*180/np.pi:7.3f}°), AngVel: {vehicle_state['angular_velocity']:+.6f} rad/s")

        if terminated or truncated:
            print("\nエピソード終了")
            break

    print()
    print("【後退テスト】ステアリング=0.0、スロットル=-0.5で50ステップ実行:")
    print("-" * 60)

    # リセット
    obs, info = env.reset()
    vehicle_state = env.vehicle.get_state()
    print(f"初期角度: {vehicle_state['angle']:.6f} rad ({vehicle_state['angle']*180/np.pi:7.3f}°)")
    print()

    for step in range(50):
        action = np.array([0.0, -0.5])  # ステアリング=0、スロットル=-0.5（後退）

        obs, reward, terminated, truncated, info = env.step(action)

        # 車両の内部状態を取得
        vehicle_state = env.vehicle.get_state()

        if step < 5 or step % 20 == 0:
            print(f"[Step {step+1:3d}] Angle: {vehicle_state['angle']:.6f} rad ({vehicle_state['angle']*180/np.pi:7.3f}°), AngVel: {vehicle_state['angular_velocity']:+.6f} rad/s")

        if terminated or truncated:
            print("\nエピソード終了")
            break

    print()
    print("=" * 60)
    print("テスト完了")
    print("=" * 60)

    env.close()


if __name__ == "__main__":
    main()
