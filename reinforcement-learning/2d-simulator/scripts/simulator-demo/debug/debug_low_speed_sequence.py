"""低速時のステアリングシーケンステスト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from src.env.minicar_env import MinicarEnv


def test_sequence(env, throttle, steps_per_phase, test_name):
    """
    左入力→無入力→左入力というシーケンスをテスト

    Args:
        env: 環境
        throttle: スロットル値
        steps_per_phase: 各フェーズのステップ数
        test_name: テスト名
    """
    print(f"\n{'='*70}")
    print(f"{test_name}")
    print(f"スロットル: {throttle:+.2f}, 各フェーズ: {steps_per_phase}ステップ")
    print('='*70)

    # リセット
    obs, info = env.reset()
    vehicle_state = env.vehicle.get_state()
    initial_angle = vehicle_state['angle']
    print(f"初期角度: {initial_angle:.6f} rad ({initial_angle*180/np.pi:+8.3f}°)")
    print()

    # フェーズ1: 左入力
    print(f"【フェーズ1】左入力 (ステアリング=-1.0) × {steps_per_phase}ステップ")
    print("-" * 70)
    phase1_start_angle = vehicle_state['angle']

    for step in range(steps_per_phase):
        action = np.array([-1.0, throttle])  # 左入力
        obs, reward, terminated, truncated, info = env.step(action)

        vehicle_state = env.vehicle.get_state()
        angle = vehicle_state['angle']
        ang_vel = vehicle_state['angular_velocity']
        speed = vehicle_state['speed']
        angle_change = angle - phase1_start_angle

        print(f"[Step {step+1:3d}] Angle: {angle:.6f} rad ({angle*180/np.pi:+8.3f}°), "
              f"Change: {angle_change*180/np.pi:+8.3f}°, "
              f"AngVel: {ang_vel:+.6f} rad/s, Speed: {speed:.2f} m/s")

        if terminated or truncated:
            print("\nエピソード終了")
            return

    phase1_end_angle = vehicle_state['angle']
    phase1_angle_change = phase1_end_angle - phase1_start_angle
    print(f"\nフェーズ1の角度変化: {phase1_angle_change*180/np.pi:+8.3f}°")
    print(f"最終角速度: {vehicle_state['angular_velocity']:+.6f} rad/s")

    # フェーズ2: 無入力
    print(f"\n【フェーズ2】無入力 (ステアリング=0.0) × {steps_per_phase}ステップ")
    print("-" * 70)
    phase2_start_angle = vehicle_state['angle']

    for step in range(steps_per_phase):
        action = np.array([0.0, throttle])  # 無入力（まっすぐ）
        obs, reward, terminated, truncated, info = env.step(action)

        vehicle_state = env.vehicle.get_state()
        angle = vehicle_state['angle']
        ang_vel = vehicle_state['angular_velocity']
        speed = vehicle_state['speed']
        angle_change = angle - phase2_start_angle

        print(f"[Step {step+1:3d}] Angle: {angle:.6f} rad ({angle*180/np.pi:+8.3f}°), "
              f"Change: {angle_change*180/np.pi:+8.3f}°, "
              f"AngVel: {ang_vel:+.6f} rad/s, Speed: {speed:.2f} m/s")

        if terminated or truncated:
            print("\nエピソード終了")
            return

    phase2_end_angle = vehicle_state['angle']
    phase2_angle_change = phase2_end_angle - phase2_start_angle
    print(f"\nフェーズ2の角度変化: {phase2_angle_change*180/np.pi:+8.3f}°")
    print(f"最終角速度: {vehicle_state['angular_velocity']:+.6f} rad/s")

    # フェーズ3: 再び左入力
    print(f"\n【フェーズ3】左入力 (ステアリング=-1.0) × {steps_per_phase}ステップ")
    print("-" * 70)
    phase3_start_angle = vehicle_state['angle']

    for step in range(steps_per_phase):
        action = np.array([-1.0, throttle])  # 左入力
        obs, reward, terminated, truncated, info = env.step(action)

        vehicle_state = env.vehicle.get_state()
        angle = vehicle_state['angle']
        ang_vel = vehicle_state['angular_velocity']
        speed = vehicle_state['speed']
        angle_change = angle - phase3_start_angle

        print(f"[Step {step+1:3d}] Angle: {angle:.6f} rad ({angle*180/np.pi:+8.3f}°), "
              f"Change: {angle_change*180/np.pi:+8.3f}°, "
              f"AngVel: {ang_vel:+.6f} rad/s, Speed: {speed:.2f} m/s")

        if terminated or truncated:
            print("\nエピソード終了")
            return

    phase3_end_angle = vehicle_state['angle']
    phase3_angle_change = phase3_end_angle - phase3_start_angle
    print(f"\nフェーズ3の角度変化: {phase3_angle_change*180/np.pi:+8.3f}°")
    print(f"最終角速度: {vehicle_state['angular_velocity']:+.6f} rad/s")

    # 全体の分析
    print(f"\n{'='*70}")
    print("分析:")
    print(f"  フェーズ1の角度変化: {phase1_angle_change*180/np.pi:+8.3f}° (期待: 負の値 = 左回転)")
    print(f"  フェーズ2の角度変化: {phase2_angle_change*180/np.pi:+8.3f}° (期待: 0に近い値)")
    print(f"  フェーズ3の角度変化: {phase3_angle_change*180/np.pi:+8.3f}° (期待: 負の値 = 左回転)")

    # フェーズ3で右回転していたら警告
    if phase3_angle_change > 0.01:
        print("\n⚠️  【警告】フェーズ3で左入力なのに右回転しています！")
        print("   これが報告されている問題です。")
    elif phase3_angle_change < -0.01:
        print("\n✓ フェーズ3は正常に左回転しています")
    else:
        print("\n⚠️  フェーズ3でほとんど回転していません")


def main():
    """デバッグテスト"""
    print("=" * 70)
    print("低速時のステアリングシーケンステスト")
    print("問題: 左入力→無入力→左入力で反対に操作されることがある")
    print("=" * 70)

    # 環境作成
    env = MinicarEnv(course_file="courses/easy/simple_oval.json", render_mode=None)

    # テスト1: 超低速
    test_sequence(env, throttle=0.1, steps_per_phase=5,
                  test_name="【テスト1】超低速 (スロットル=0.1)")

    # テスト2: 低速
    test_sequence(env, throttle=0.2, steps_per_phase=5,
                  test_name="【テスト2】低速 (スロットル=0.2)")

    # テスト3: やや低速
    test_sequence(env, throttle=0.3, steps_per_phase=5,
                  test_name="【テスト3】やや低速 (スロットル=0.3)")

    # テスト4: 通常速度（比較用）
    test_sequence(env, throttle=0.5, steps_per_phase=5,
                  test_name="【テスト4】通常速度 (スロットル=0.5)")

    # テスト5: 超低速で長めのシーケンス
    test_sequence(env, throttle=0.1, steps_per_phase=10,
                  test_name="【テスト5】超低速 + 長めのシーケンス (スロットル=0.1)")

    # テスト6: 超低速で短いシーケンス
    test_sequence(env, throttle=0.1, steps_per_phase=3,
                  test_name="【テスト6】超低速 + 短いシーケンス (スロットル=0.1)")

    print()
    print("=" * 70)
    print("テスト完了")
    print("=" * 70)

    env.close()


if __name__ == "__main__":
    main()
