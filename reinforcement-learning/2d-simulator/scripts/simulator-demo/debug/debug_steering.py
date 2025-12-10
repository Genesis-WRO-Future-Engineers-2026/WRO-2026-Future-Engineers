"""ステアリング入力のデバッグスクリプト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from src.env.minicar_env import MinicarEnv


def test_steering(env, steering, throttle, steps, test_name):
    """ステアリングテスト"""
    print(f"\n{'='*70}")
    print(f"{test_name}")
    print(f"ステアリング: {steering:+.2f}, スロットル: {throttle:+.2f}, {steps}ステップ")
    print('='*70)

    # リセット
    obs, info = env.reset()
    vehicle_state = env.vehicle.get_state()
    initial_angle = vehicle_state['angle']
    print(f"初期角度: {initial_angle:.6f} rad ({initial_angle*180/np.pi:+8.3f}°)")
    print()

    for step in range(steps):
        action = np.array([steering, throttle])
        obs, reward, terminated, truncated, info = env.step(action)

        # 車両の内部状態を取得
        vehicle_state = env.vehicle.get_state()
        angle = vehicle_state['angle']
        ang_vel = vehicle_state['angular_velocity']
        speed = vehicle_state['speed']

        # 角度の変化を計算
        angle_change = angle - initial_angle

        if step < 10 or step % 10 == 0:
            print(f"[Step {step+1:3d}] Angle: {angle:.6f} rad ({angle*180/np.pi:+8.3f}°), "
                  f"Change: {angle_change*180/np.pi:+8.3f}°, "
                  f"AngVel: {ang_vel:+.6f} rad/s, Speed: {speed:.2f} m/s")

        if terminated or truncated:
            print("\nエピソード終了")
            break

    # 最終結果
    final_angle_change = angle - initial_angle
    print()
    print(f"最終角度変化: {final_angle_change*180/np.pi:+8.3f}°")

    # 左入力（負のステアリング）で角度が減少（右回転）したら警告
    if steering < 0 and final_angle_change < -0.01:
        print("⚠️  警告: 左入力なのに右回転しています！")
    # 右入力（正のステアリング）で角度が増加（左回転）したら警告
    elif steering > 0 and final_angle_change > 0.01:
        print("⚠️  警告: 右入力なのに左回転しています！")

    return final_angle_change


def main():
    """デバッグテスト"""
    print("=" * 70)
    print("ステアリング入力のデバッグテスト")
    print("=" * 70)

    # 環境作成
    env = MinicarEnv(course_file="courses/easy/simple_oval.json", render_mode=None)

    # テスト1: 静止状態から左入力（スロットル0）
    test_steering(env, steering=-1.0, throttle=0.0, steps=30,
                  test_name="【テスト1】静止状態 + 左入力")

    # テスト2: 前進しながら左入力
    test_steering(env, steering=-1.0, throttle=0.5, steps=30,
                  test_name="【テスト2】前進 + 左入力")

    # テスト3: 後退しながら左入力
    test_steering(env, steering=-1.0, throttle=-0.5, steps=30,
                  test_name="【テスト3】後退 + 左入力")

    # テスト4: 前進しながら右入力（比較用）
    test_steering(env, steering=+1.0, throttle=0.5, steps=30,
                  test_name="【テスト4】前進 + 右入力（比較用）")

    # テスト5: 後退しながら右入力（比較用）
    test_steering(env, steering=+1.0, throttle=-0.5, steps=30,
                  test_name="【テスト5】後退 + 右入力（比較用）")

    # テスト6: 弱い左入力
    test_steering(env, steering=-0.3, throttle=0.5, steps=30,
                  test_name="【テスト6】前進 + 弱い左入力")

    print()
    print("=" * 70)
    print("テスト完了")
    print("=" * 70)

    env.close()


if __name__ == "__main__":
    main()
