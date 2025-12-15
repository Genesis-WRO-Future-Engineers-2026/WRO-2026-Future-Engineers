"""CollisionListenerの単体テスト"""

import pytest
from Box2D import b2World, b2Vec2
from src.physics.collision_listener import CollisionListener


def test_collision_listener_initialization():
    """CollisionListenerの初期化テスト"""
    listener = CollisionListener()
    assert listener.is_collision() == False


def test_collision_listener_reset():
    """CollisionListenerのリセットテスト"""
    listener = CollisionListener()
    listener.collision_detected = True
    assert listener.is_collision() == True

    listener.reset()
    assert listener.is_collision() == False


def test_vehicle_wall_collision_detection():
    """車両と壁の衝突検出テスト"""
    # Box2D世界を作成
    listener = CollisionListener()
    world = b2World(gravity=(0, 0), doSleep=True)
    world.contactListener = listener

    # 車両ボディを作成
    vehicle_body = world.CreateDynamicBody(
        position=(0, 0)
    )
    vehicle_body.userData = "vehicle"
    vehicle_body.CreatePolygonFixture(box=(0.2, 0.1), density=1.0)

    # 壁ボディを作成（車両のすぐ近く）
    wall_body = world.CreateStaticBody(
        position=(0.5, 0)
    )
    wall_body.userData = "wall"
    wall_body.CreatePolygonFixture(box=(0.1, 1.0))

    # 衝突前は検出されていない
    assert listener.is_collision() == False

    # 車両を壁に向かって移動
    vehicle_body.linearVelocity = b2Vec2(10, 0)

    # 物理シミュレーションを進める
    for _ in range(100):
        world.Step(1.0/60.0, 8, 3)
        if listener.is_collision():
            break

    # 衝突が検出されたことを確認
    assert listener.is_collision() == True


def test_no_collision_without_wall():
    """壁がない場合は衝突が検出されないテスト"""
    listener = CollisionListener()
    world = b2World(gravity=(0, 0), doSleep=True)
    world.contactListener = listener

    # 車両ボディのみを作成
    vehicle_body = world.CreateDynamicBody(position=(0, 0))
    vehicle_body.userData = "vehicle"
    vehicle_body.CreatePolygonFixture(box=(0.2, 0.1), density=1.0)

    # 車両を移動
    vehicle_body.linearVelocity = b2Vec2(10, 0)

    # 物理シミュレーションを進める
    for _ in range(100):
        world.Step(1.0/60.0, 8, 3)

    # 衝突は検出されない
    assert listener.is_collision() == False


def test_vehicle_to_vehicle_no_collision():
    """車両同士の接触は衝突として検出されないテスト"""
    listener = CollisionListener()
    world = b2World(gravity=(0, 0), doSleep=True)
    world.contactListener = listener

    # 車両1
    vehicle1_body = world.CreateDynamicBody(position=(0, 0))
    vehicle1_body.userData = "vehicle"
    vehicle1_body.CreatePolygonFixture(box=(0.2, 0.1), density=1.0)

    # 車両2
    vehicle2_body = world.CreateDynamicBody(position=(0.5, 0))
    vehicle2_body.userData = "vehicle"
    vehicle2_body.CreatePolygonFixture(box=(0.2, 0.1), density=1.0)

    # 車両1を車両2に向かって移動
    vehicle1_body.linearVelocity = b2Vec2(10, 0)

    # 物理シミュレーションを進める
    for _ in range(100):
        world.Step(1.0/60.0, 8, 3)

    # 壁との衝突ではないので検出されない
    assert listener.is_collision() == False
