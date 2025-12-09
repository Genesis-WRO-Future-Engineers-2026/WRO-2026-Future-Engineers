"""PhysicsWorldクラスのテスト"""

import pytest
from src.physics.box2d_wrapper import PhysicsWorld


def test_physics_world_creation():
    """PhysicsWorldが正しく作成されるか"""
    world = PhysicsWorld()
    assert world is not None
    assert world.world is not None


def test_add_static_box():
    """静的な矩形を追加"""
    world = PhysicsWorld()
    box = world.add_static_box((5, 5), 1, 1)

    assert box is not None
    assert abs(box.position.x - 5) < 0.01
    assert abs(box.position.y - 5) < 0.01


def test_add_wall_segment():
    """壁セグメントを追加"""
    world = PhysicsWorld()
    wall = world.add_wall_segment((0, 0), (10, 0))

    assert wall is not None
    # 中点に配置されているか確認
    assert abs(wall.position.x - 5) < 0.01
    assert abs(wall.position.y - 0) < 0.01


def test_step_simulation():
    """シミュレーションステップの実行"""
    world = PhysicsWorld()

    # 動的ボディを追加
    body = world.world.CreateDynamicBody(position=(0, 0))
    body.CreateCircleFixture(radius=0.5, density=1)

    # 初期位置
    initial_x = body.position.x

    # 力を加えながらシミュレーション
    for _ in range(60):
        body.ApplyForceToCenter((10, 0), True)
        world.step()

    # 移動したか確認
    assert body.position.x > initial_x
