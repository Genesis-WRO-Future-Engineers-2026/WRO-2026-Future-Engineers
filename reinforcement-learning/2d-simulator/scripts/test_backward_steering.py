"""後退時のステアリング挙動をテスト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from src.env.minicar_env import MinicarEnv


def test_backward_steering():
    """後退時のステアリングテスト"""
    print("=" * 70)
    print("後退時のステアリング挙動テスト")
    print("=" * 70)
    print()

    env = MinicarEnv(course_file="courses/easy/simple_oval.json", render_mode=None)

    # テスト1: 前進 + 左入力
    print("【テスト1】前進 + 左入力（ステアリング=-1.0, スロットル=0.5）")
    print("-" * 70)
    obs, info = env.reset()
    initial_angle = env.vehicle.get_state()['angle']

    for step in range(20):
        action = np.array([-1.0, 0.5])
        obs, reward, terminated, truncated, info = env.step(action)

        if step % 5 == 0:
            state = env.vehicle.get_state()
            angle_change = state['angle'] - initial_angle
            print(f"[Step {step+1:2d}] 角度変化: {angle_change*180/np.pi:+7.2f}° (期待: 負 = 左回転)")

    final_angle_change = env.vehicle.get_state()['angle'] - initial_angle
    print(f"最終角度変化: {final_angle_change*180/np.pi:+7.2f}°")
    print(f"結果: {'✓ 左回転' if final_angle_change < 0 else '✗ 右回転'}")
    print()

    # テスト2: 後退 + 左入力（現在の実装）
    print("【テスト2】後退 + 左入力（ステアリング=-1.0, スロットル=-0.5）")
    print("現在の実装: 後退時はステアリングを反転 → 物理的には右入力として動作")
    print("-" * 70)
    obs, info = env.reset()
    initial_angle = env.vehicle.get_state()['angle']

    for step in range(20):
        action = np.array([-1.0, -0.5])
        obs, reward, terminated, truncated, info = env.step(action)

        if step % 5 == 0:
            state = env.vehicle.get_state()
            angle_change = state['angle'] - initial_angle
            print(f"[Step {step+1:2d}] 角度変化: {angle_change*180/np.pi:+7.2f}° (反転により左回転)")

    final_angle_change = env.vehicle.get_state()['angle'] - initial_angle
    print(f"最終角度変化: {final_angle_change*180/np.pi:+7.2f}°")
    print(f"結果: {'✓ 左回転（反転により）' if final_angle_change < 0 else '✗ 右回転'}")
    print()

    # テスト3: 後退 + 右入力（現在の実装）
    print("【テスト3】後退 + 右入力（ステアリング=+1.0, スロットル=-0.5）")
    print("現在の実装: 後退時はステアリングを反転 → 物理的には左入力として動作")
    print("-" * 70)
    obs, info = env.reset()
    initial_angle = env.vehicle.get_state()['angle']

    for step in range(20):
        action = np.array([+1.0, -0.5])
        obs, reward, terminated, truncated, info = env.step(action)

        if step % 5 == 0:
            state = env.vehicle.get_state()
            angle_change = state['angle'] - initial_angle
            print(f"[Step {step+1:2d}] 角度変化: {angle_change*180/np.pi:+7.2f}° (反転により右回転)")

    final_angle_change = env.vehicle.get_state()['angle'] - initial_angle
    print(f"最終角度変化: {final_angle_change*180/np.pi:+7.2f}°")
    print(f"結果: {'✓ 右回転（反転により）' if final_angle_change > 0 else '✗ 左回転'}")
    print()

    print("=" * 70)
    print("分析:")
    print("=" * 70)
    print("現在の実装では、後退時に以下の問題があります：")
    print()
    print("1. 強化学習での問題:")
    print("   - スロットルの符号でステアリングの意味が変わる")
    print("   - エージェントが余分な複雑性を学習する必要がある")
    print("   - 行動空間が非線形になる")
    print()
    print("2. 物理的な問題:")
    print("   - Bicycle Modelの物理挙動を歪めている")
    print("   - 実際のミニカーでは後退時に物理的に逆方向に曲がる")
    print()
    print("推奨: 強化学習用途では、後退時のステアリング反転を削除すべき")
    print("=" * 70)

    env.close()


if __name__ == "__main__":
    test_backward_steering()
