"""Box2D物理エンジンのラッパークラス"""

from Box2D import b2World, b2Vec2, b2Body, b2PolygonShape
from typing import List, Tuple


class PhysicsWorld:
    """Box2D物理世界の管理クラス"""

    def __init__(self, gravity: Tuple[float, float] = (0, 0)):
        """
        Args:
            gravity: 重力ベクトル (x, y)。2Dレースなので通常は(0, 0)
        """
        self.world = b2World(gravity=b2Vec2(*gravity), doSleep=True)
        self.time_step = 1.0 / 60.0  # 60Hz
        self.vel_iters = 8  # 速度反復回数
        self.pos_iters = 3  # 位置反復回数

    def step(self):
        """物理シミュレーションを1ステップ進める"""
        self.world.Step(self.time_step, self.vel_iters, self.pos_iters)

    def add_static_box(
        self, center: Tuple[float, float], width: float, height: float
    ) -> b2Body:
        """
        静的な矩形を追加（壁などに使用）

        Args:
            center: 中心座標 (x, y)
            width: 幅
            height: 高さ

        Returns:
            作成したBox2Dのbody
        """
        body = self.world.CreateStaticBody(
            position=b2Vec2(*center), shapes=b2PolygonShape(box=(width / 2, height / 2))
        )
        return body

    def add_static_polygon(self, vertices: List[Tuple[float, float]]) -> b2Body:
        """
        静的なポリゴンを追加

        Args:
            vertices: 頂点のリスト [(x1, y1), (x2, y2), ...]

        Returns:
            作成したBox2Dのbody
        """
        # Box2Dは凸ポリゴンのみサポート
        vertices_b2 = [b2Vec2(*v) for v in vertices]
        body = self.world.CreateStaticBody(shapes=b2PolygonShape(vertices=vertices_b2))
        return body

    def add_wall_segment(
        self, v1: Tuple[float, float], v2: Tuple[float, float], thickness: float = 0.1
    ) -> b2Body:
        """
        2点間に壁セグメントを作成

        Args:
            v1: 始点 (x, y)
            v2: 終点 (x, y)
            thickness: 壁の厚み

        Returns:
            作成したBox2Dのbody
        """
        import numpy as np

        # 中点
        center = [(v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2]

        # 長さと角度
        dx = v2[0] - v1[0]
        dy = v2[1] - v1[1]
        length = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)

        # 静的ボディ作成
        body = self.world.CreateStaticBody(
            position=b2Vec2(*center),
            angle=angle,
            shapes=b2PolygonShape(box=(length / 2, thickness / 2)),
        )
        return body
