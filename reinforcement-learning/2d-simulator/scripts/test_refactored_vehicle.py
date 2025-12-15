"""リファクタリング後のVehicleの動作確認テスト"""

import sys
import os

# PYTHONPATHの設定
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Box2D import b2World

# サブモジュールからインポート
from src.env.vehicle import VehicleConfig, PhysicsParameters

# Vehicleクラスは別ファイル（現在のディレクトリ構成の問題を回避）
import importlib.util
spec = importlib.util.spec_from_file_location(
    "vehicle_main",
    os.path.join(os.path.dirname(__file__), '..', 'src', 'env', 'vehicle.py')
)
vehicle_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vehicle_main)
Vehicle = vehicle_main.Vehicle


def test_basic_functionality():
    """基本的な機能のテスト"""
    print("=" * 60)
    print("Vehicle基本機能のテスト")
    print("=" * 60)

    # 物理世界を作成
    world = b2World(gravity=(0, 0))

    # 車両を作成
    print("\n[TEST 1] 車両の作成...")
    try:
        vehicle = Vehicle(world, start_pos=(0.0, 0.0), start_angle=0.0)
        print("✅ 車両の作成に成功")
    except Exception as e:
        print(f"❌ 車両の作成に失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 状態を取得
    print("\n[TEST 2] 状態の取得...")
    try:
        state = vehicle.get_state()
        assert state["position"] == (0.0, 0.0)
        assert state["angle"] == 0.0
        print(f"✅ 状態取得成功: position={state['position']}, angle={state['angle']:.2f}")
    except Exception as e:
        print(f"❌ 状態取得に失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 制御入力を適用
    print("\n[TEST 3] 制御入力の適用...")
    try:
        vehicle.apply_control(steering=0.5, throttle=1.0)
        world.Step(1/60, 6, 2)
        state = vehicle.get_state()
        print(f"✅ 制御入力成功: speed={state['speed']:.2f}")
    except Exception as e:
        print(f"❌ 制御入力に失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    # リセット
    print("\n[TEST 4] リセット...")
    try:
        vehicle.reset(position=(1.0, 1.0), angle=1.57)
        state = vehicle.get_state()
        assert abs(state["position"][0] - 1.0) < 0.01
        assert abs(state["position"][1] - 1.0) < 0.01
        print("✅ リセット成功")
    except Exception as e:
        print(f"❌ リセットに失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("すべてのテストに成功しました！")
    print("=" * 60)
    return True


def test_backward_compatibility():
    """後方互換性のテスト"""
    print("\n" + "=" * 60)
    print("後方互換性のテスト")
    print("=" * 60)

    print("\n[TEST] 既存の使用方法が動作するか...")
    try:
        # 既存の使用方法
        world = b2World(gravity=(0, 0))
        vehicle = Vehicle(world, start_pos=(0.0, 0.0), start_angle=0.0)

        vehicle.apply_control(steering=0.0, throttle=0.5)
        world.Step(1/60, 6, 2)
        vehicle.reset(position=(0.0, 0.0), angle=0.0)

        print("✅ 後方互換性テスト成功")
        return True
    except Exception as e:
        print(f"❌ 後方互換性テストに失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custom_config():
    """カスタム設定のテスト"""
    print("\n" + "=" * 60)
    print("カスタム設定のテスト")
    print("=" * 60)

    print("\n[TEST] カスタム設定を使用...")
    try:
        # カスタム設定を作成
        custom_config = VehicleConfig.create_custom(
            width=0.2,
            length=0.5,
            max_steering_angle=0.6,
        )

        custom_params = PhysicsParameters.create_default()
        custom_params.mass = 2.0

        # 車両を作成
        world = b2World(gravity=(0, 0))
        vehicle = Vehicle(
            world,
            start_pos=(0.0, 0.0),
            config=custom_config,
            physics_params=custom_params,
        )

        assert vehicle.config.width == 0.2
        assert vehicle.config.length == 0.5
        assert vehicle.physics_params.mass == 2.0

        print("✅ カスタム設定テスト成功")
        return True
    except Exception as e:
        print(f"❌ カスタム設定テストに失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_domain_randomization():
    """Domain Randomizationのテスト"""
    print("\n" + "=" * 60)
    print("Domain Randomizationのテスト")
    print("=" * 60)

    print("\n[TEST] PhysicsParametersでリセット...")
    try:
        world = b2World(gravity=(0, 0))
        vehicle = Vehicle(world, start_pos=(0.0, 0.0))

        # Domain Randomization用のパラメータを作成
        randomized_params = PhysicsParameters(
            mass=1.8,
            friction=0.8,
            max_motor_force=25.0,
        )

        vehicle.reset(position=(0.0, 0.0), physics_params=randomized_params)

        assert vehicle.physics_params.mass == 1.8
        assert vehicle.physics_params.friction == 0.8
        assert vehicle.controller.max_motor_force == 25.0

        print("✅ Domain Randomizationテスト成功")
        return True
    except Exception as e:
        print(f"❌ Domain Randomizationテストに失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_old_style_reset():
    """古いスタイルのreset()のテスト（後方互換性）"""
    print("\n" + "=" * 60)
    print("古いスタイルのreset()のテスト")
    print("=" * 60)

    print("\n[TEST] 古いスタイルのreset()...")
    try:
        world = b2World(gravity=(0, 0))
        vehicle = Vehicle(world, start_pos=(0.0, 0.0))

        # 古いスタイルのreset()（個別パラメータ指定）
        vehicle.reset(
            position=(0.0, 0.0),
            angle=0.0,
            mass=1.8,
            friction=0.8,
            linear_damping=0.6,
            angular_damping=0.9,
            max_motor_force=25.0,
            max_lateral_impulse=3.0,
        )

        assert vehicle.physics_params.mass == 1.8
        assert vehicle.physics_params.friction == 0.8
        assert vehicle.physics_params.linear_damping == 0.6
        assert vehicle.physics_params.angular_damping == 0.9
        assert vehicle.controller.max_motor_force == 25.0
        assert vehicle.controller.max_lateral_impulse == 3.0

        print("✅ 古いスタイルのreset()テスト成功")
        return True
    except Exception as e:
        print(f"❌ 古いスタイルのreset()テストに失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = True

    # 各テストを実行
    if not test_basic_functionality():
        success = False

    if not test_backward_compatibility():
        success = False

    if not test_custom_config():
        success = False

    if not test_domain_randomization():
        success = False

    if not test_old_style_reset():
        success = False

    # 結果
    print("\n" + "=" * 60)
    if success:
        print("🎉 すべてのテストに合格しました！")
    else:
        print("⚠️  一部のテストに失敗しました")
    print("=" * 60)

    sys.exit(0 if success else 1)
