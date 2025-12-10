"""車両の内部動作を詳細にデバッグするスクリプト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from src.env.minicar_env import MinicarEnv


def test_detailed(env, throttle):
    """詳細なデバッグテスト"""
    print(f"\n{'='*70}")
    print(f"詳細デバッグテスト (スロットル={throttle})")
    print('='*70)

    # リセット
    obs, info = env.reset()
    vehicle_state = env.vehicle.get_state()
    initial_angle = vehicle_state['angle']
    print(f"初期角度: {initial_angle:.6f} rad")
    print()

    # フェーズ1: 左入力 × 3ステップ
    print("【フェーズ1】左入力 × 3ステップ")
    print("-" * 70)
    for step in range(3):
        action = np.array([-1.0, throttle])

        # デバッグ出力を有効にして実行
        vehicle_state_before = env.vehicle.get_state()
        print(f"\n[Step {step+1}] 実行前:")
        print(f"  ステアリング: -1.0, スロットル: {throttle}")
        print(f"  角度: {vehicle_state_before['angle']:.6f} rad")
        print(f"  角速度: {vehicle_state_before['angular_velocity']:+.6f} rad/s")

        # apply_controlをデバッグモードで呼び出す
        env.vehicle.apply_control(-1.0, throttle, debug=True)

        # 物理シミュレーションを1ステップ進める
        for _ in range(env.physics_steps_per_action):
            env.world.Step(env.time_step, 6, 2)

        vehicle_state_after = env.vehicle.get_state()
        print(f"  実行後:")
        print(f"  角度: {vehicle_state_after['angle']:.6f} rad (変化: {(vehicle_state_after['angle']-vehicle_state_before['angle'])*180/np.pi:+.3f}°)")
        print(f"  角速度: {vehicle_state_after['angular_velocity']:+.6f} rad/s")

    # フェーズ2: 無入力 × 3ステップ
    print("\n\n【フェーズ2】無入力 × 3ステップ")
    print("-" * 70)
    for step in range(3):
        action = np.array([0.0, throttle])

        vehicle_state_before = env.vehicle.get_state()
        print(f"\n[Step {step+1}] 実行前:")
        print(f"  ステアリング: 0.0, スロットル: {throttle}")
        print(f"  角度: {vehicle_state_before['angle']:.6f} rad")
        print(f"  角速度: {vehicle_state_before['angular_velocity']:+.6f} rad/s")

        # apply_controlをデバッグモードで呼び出す
        env.vehicle.apply_control(0.0, throttle, debug=True)

        # 物理シミュレーションを1ステップ進める
        for _ in range(env.physics_steps_per_action):
            env.world.Step(env.time_step, 6, 2)

        vehicle_state_after = env.vehicle.get_state()
        print(f"  実行後:")
        print(f"  角度: {vehicle_state_after['angle']:.6f} rad (変化: {(vehicle_state_after['angle']-vehicle_state_before['angle'])*180/np.pi:+.3f}°)")
        print(f"  角速度: {vehicle_state_after['angular_velocity']:+.6f} rad/s")

    # フェーズ3: 左入力 × 3ステップ
    print("\n\n【フェーズ3】左入力 × 3ステップ")
    print("-" * 70)
    for step in range(3):
        action = np.array([-1.0, throttle])

        vehicle_state_before = env.vehicle.get_state()
        print(f"\n[Step {step+1}] 実行前:")
        print(f"  ステアリング: -1.0, スロットル: {throttle}")
        print(f"  角度: {vehicle_state_before['angle']:.6f} rad")
        print(f"  角速度: {vehicle_state_before['angular_velocity']:+.6f} rad/s")

        # apply_controlをデバッグモードで呼び出す
        env.vehicle.apply_control(-1.0, throttle, debug=True)

        # 物理シミュレーションを1ステップ進める
        for _ in range(env.physics_steps_per_action):
            env.world.Step(env.time_step, 6, 2)

        vehicle_state_after = env.vehicle.get_state()
        print(f"  実行後:")
        print(f"  角度: {vehicle_state_after['angle']:.6f} rad (変化: {(vehicle_state_after['angle']-vehicle_state_before['angle'])*180/np.pi:+.3f}°)")
        print(f"  角速度: {vehicle_state_after['angular_velocity']:+.6f} rad/s")


def main():
    """デバッグテスト"""
    print("=" * 70)
    print("車両の内部動作の詳細デバッグ")
    print("=" * 70)

    # 環境作成
    env = MinicarEnv(course_file="courses/easy/simple_oval.json", render_mode=None)

    # 超低速でテスト
    test_detailed(env, throttle=0.1)

    env.close()


if __name__ == "__main__":
    main()
