"""PhysicsWorldのCollisionListener統合テスト"""

import pytest
from Box2D import b2Vec2
from src.physics.box2d_wrapper import PhysicsWorld
from src.physics.collision_listener import CollisionListener


def test_physics_world_with_collision_listener():
    """PhysicsWorldにCollisionListenerを統合したテスト"""
    listener = CollisionListener()
    world = PhysicsWorld(collision_listener=listener)

    # 衝突リスナーが正しく登録されているか
    assert world.collision_listener == listener
    assert world.world.contactListener == listener


def test_physics_world_without_collision_listener():
    """PhysicsWorldをCollisionListenerなしで作成できるテスト"""
    world = PhysicsWorld()

    # リスナーなしでも動作する
    assert world.collision_listener is None
    assert world.has_collision() == False


def test_physics_world_collision_detection():
    """PhysicsWorldでの衝突検出テスト"""
    listener = CollisionListener()
    world = PhysicsWorld(collision_listener=listener)

    # 車両を作成
    vehicle_body = world.world.CreateDynamicBody(position=(0, 0))
    vehicle_body.userData = "vehicle"
    vehicle_body.CreatePolygonFixture(box=(0.2, 0.1), density=1.0)

    # 壁を作成
    wall_body = world.world.CreateStaticBody(position=(0.5, 0))
    wall_body.userData = "wall"
    wall_body.CreatePolygonFixture(box=(0.1, 1.0))

    # 初期状態
    assert world.has_collision() == False

    # 車両を壁に向かって移動
    vehicle_body.linearVelocity = b2Vec2(10, 0)

    # 衝突するまでシミュレーション
    for _ in range(100):
        world.step()
        if world.has_collision():
            break

    # 衝突が検出されたことを確認
    assert world.has_collision() == True


def test_physics_world_reset_collision():
    """PhysicsWorldの衝突フラグリセットテスト"""
    listener = CollisionListener()
    world = PhysicsWorld(collision_listener=listener)

    # 車両と壁を作成
    vehicle_body = world.world.CreateDynamicBody(position=(0, 0))
    vehicle_body.userData = "vehicle"
    vehicle_body.CreatePolygonFixture(box=(0.2, 0.1), density=1.0)

    wall_body = world.world.CreateStaticBody(position=(0.5, 0))
    wall_body.userData = "wall"
    wall_body.CreatePolygonFixture(box=(0.1, 1.0))

    # 衝突させる
    vehicle_body.linearVelocity = b2Vec2(10, 0)
    for _ in range(100):
        world.step()
        if world.has_collision():
            break

    assert world.has_collision() == True

    # リセット
    world.reset_collision()
    assert world.has_collision() == False


def test_physics_world_multiple_collisions():
    """PhysicsWorldで複数回の衝突検出テスト"""
    listener = CollisionListener()
    world = PhysicsWorld(collision_listener=listener)

    # 車両と壁を作成
    vehicle_body = world.world.CreateDynamicBody(position=(0, 0))
    vehicle_body.userData = "vehicle"
    vehicle_body.CreatePolygonFixture(box=(0.2, 0.1), density=1.0)

    wall_body = world.world.CreateStaticBody(position=(0.5, 0))
    wall_body.userData = "wall"
    wall_body.CreatePolygonFixture(box=(0.1, 1.0))

    # 1回目の衝突
    vehicle_body.linearVelocity = b2Vec2(10, 0)
    for _ in range(100):
        world.step()
        if world.has_collision():
            break

    assert world.has_collision() == True

    # リセット後、再度衝突
    world.reset_collision()
    vehicle_body.position = b2Vec2(0, 0)
    vehicle_body.linearVelocity = b2Vec2(10, 0)

    for _ in range(100):
        world.step()
        if world.has_collision():
            break

    # 2回目も検出される
    assert world.has_collision() == True
