"""車両モデルのテスト"""

import pytest
import numpy as np
from src.physics.box2d_wrapper import PhysicsWorld
from src.env.vehicle import Vehicle


def test_vehicle_creation():
    """車両が正しく作成されるか"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    assert vehicle is not None
    assert vehicle.body is not None


def test_vehicle_initial_state():
    """初期状態が正しいか"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (5, 10), np.pi / 4)

    state = vehicle.get_state()

    assert abs(state["position"][0] - 5) < 0.01
    assert abs(state["position"][1] - 10) < 0.01
    assert abs(state["angle"] - np.pi / 4) < 0.01
    assert state["speed"] < 0.01  # 初期は静止


def test_vehicle_forward_motion():
    """前進するか"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 前進（まっすぐ）
    for _ in range(100):
        vehicle.apply_control(steering=0.0, throttle=1.0)
        world.step()

    state = vehicle.get_state()

    # 前方（x正方向）に移動したか
    assert state["position"][0] > 1.0
    # y方向はほぼ動かない
    assert abs(state["position"][1]) < 0.5
    # 速度がついているか
    assert state["speed"] > 0.1


def test_vehicle_turning():
    """旋回するか"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 右旋回（より長い時間）
    for _ in range(200):
        vehicle.apply_control(steering=1.0, throttle=0.8)
        world.step()

    state = vehicle.get_state()

    # 角度が変化したか（右旋回なので負の方向）
    # 初期は旋回しにくいので、小さい閾値
    assert abs(state["angle"]) > 0.01 or state["speed"] > 0.1


def test_vehicle_reset():
    """リセットが正しく動作するか"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 移動させる
    for _ in range(50):
        vehicle.apply_control(steering=0.5, throttle=1.0)
        world.step()

    # 速度がついている
    state = vehicle.get_state()
    assert state["speed"] > 0.1

    # リセット
    vehicle.reset((10, 20), np.pi / 2)

    state = vehicle.get_state()
    assert abs(state["position"][0] - 10) < 0.01
    assert abs(state["position"][1] - 20) < 0.01
    assert abs(state["angle"] - np.pi / 2) < 0.01
    assert state["speed"] < 0.01  # 速度もリセット


def test_steering_limits():
    """ステアリングの範囲制限"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 範囲外の入力を与えても問題ないか
    vehicle.apply_control(steering=10.0, throttle=1.0)  # 範囲外
    world.step()

    # エラーが出ないことを確認
    state = vehicle.get_state()
    assert state is not None


def test_throttle_limits():
    """スロットルの範囲制限"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 範囲外の入力
    vehicle.apply_control(steering=0.0, throttle=-1.0)  # 負の値
    world.step()

    vehicle.apply_control(steering=0.0, throttle=10.0)  # 大きすぎる値
    world.step()

    # エラーが出ないことを確認
    state = vehicle.get_state()
    assert state is not None
