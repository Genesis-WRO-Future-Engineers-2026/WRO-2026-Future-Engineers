"""Box2D基本機能のテスト"""

import pytest
from Box2D import b2World, b2Vec2


def test_box2d_installation():
    """Box2Dが正しくインストールされているか確認"""
    world = b2World(gravity=(0, 0), doSleep=True)
    assert world is not None


def test_create_body():
    """簡単なボディを作成してシミュレーション"""
    world = b2World(gravity=(0, 0))
    body = world.CreateDynamicBody(position=(0, 0))
    body.CreateCircleFixture(radius=1, density=1)

    # シミュレーション実行
    for _ in range(60):
        world.Step(1 / 60, 6, 2)

    assert body is not None
    # 重力がないので位置は変わらない
    assert abs(body.position.x) < 0.01
    assert abs(body.position.y) < 0.01


def test_apply_force():
    """力を加えてボディが動くか確認"""
    world = b2World(gravity=(0, 0))
    body = world.CreateDynamicBody(position=(0, 0))
    body.CreateCircleFixture(radius=1, density=1)

    # 右方向に力を加える
    for _ in range(60):
        body.ApplyForceToCenter(b2Vec2(10, 0), True)
        world.Step(1 / 60, 6, 2)

    # 右方向に移動したか確認
    assert body.position.x > 0.1
    assert abs(body.position.y) < 0.01
