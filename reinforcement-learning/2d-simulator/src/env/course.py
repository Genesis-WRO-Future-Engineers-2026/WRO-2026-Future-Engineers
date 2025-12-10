"""コース定義とロード"""

import json
from typing import List, Tuple, Dict, Optional
from Box2D import b2World, b2Vec2
import numpy as np


class Course:
    """レースコースの管理クラス"""

    def __init__(self, course_file: str):
        """
        Args:
            course_file: コース定義ファイル（JSON）のパス
        """
        with open(course_file, "r") as f:
            self.data = json.load(f)

        self.walls = []
        self.checkpoints = []

    def create_walls(self, world: b2World):
        """
        Box2Dの静的bodyとして壁を生成

        Args:
            world: Box2Dの物理世界
        """
        for wall_data in self.data.get("walls", []):
            if wall_data["type"] == "polygon":
                vertices = wall_data["vertices"]
                # ポリゴンの各辺を壁セグメントとして作成
                self._create_polygon_walls(world, vertices)
            elif wall_data["type"] == "box":
                # 矩形の壁
                center = wall_data["center"]
                width = wall_data["width"]
                height = wall_data["height"]
                self._create_box_walls(world, center, width, height)

    def _create_polygon_walls(
        self, world: b2World, vertices: List[List[float]]
    ):
        """ポリゴンの辺を壁として作成"""
        for i in range(len(vertices)):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % len(vertices)]
            wall = self._create_wall_segment(world, v1, v2)
            self.walls.append(wall)

    def _create_box_walls(
        self,
        world: b2World,
        center: List[float],
        width: float,
        height: float,
    ):
        """矩形の壁を作成"""
        x, y = center
        half_w = width / 2
        half_h = height / 2

        # 4辺
        vertices = [
            [x - half_w, y - half_h],
            [x + half_w, y - half_h],
            [x + half_w, y + half_h],
            [x - half_w, y + half_h],
        ]
        self._create_polygon_walls(world, vertices)

    def _create_wall_segment(
        self,
        world: b2World,
        v1: List[float],
        v2: List[float],
        thickness: float = 0.1,
    ):
        """2点間に壁セグメントを作成"""
        # 中点
        center = [(v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2]

        # 長さと角度
        dx = v2[0] - v1[0]
        dy = v2[1] - v1[1]
        length = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)

        # 静的ボディ作成
        from Box2D import b2PolygonShape

        body = world.CreateStaticBody(
            position=b2Vec2(*center),
            angle=angle,
            shapes=b2PolygonShape(box=(length / 2, thickness / 2)),
        )
        return body

    def get_start_pose(self) -> Tuple[Tuple[float, float], float]:
        """
        スタート位置と角度を取得

        Returns:
            (position, angle)
        """
        start_pos = tuple(self.data["start_position"])
        start_angle = self.data.get("start_angle", 0.0)
        return start_pos, start_angle

    def get_goal_info(self) -> Tuple[Tuple[float, float], float]:
        """
        ゴール位置と半径を取得

        Returns:
            (position, radius)
        """
        goal_pos = tuple(self.data["goal_position"])
        goal_radius = self.data.get("goal_radius", 0.5)
        return goal_pos, goal_radius

    def check_goal(self, position: Tuple[float, float]) -> bool:
        """
        ゴールに到達したか判定

        Args:
            position: 車両の位置 (x, y)

        Returns:
            ゴールに到達したかどうか
        """
        goal_pos, goal_radius = self.get_goal_info()
        distance = np.sqrt(
            (position[0] - goal_pos[0]) ** 2 + (position[1] - goal_pos[1]) ** 2
        )
        return distance <= goal_radius

    def get_checkpoints(self) -> List[Dict]:
        """
        チェックポイントのリストを取得

        Returns:
            チェックポイントのリスト
        """
        return self.data.get("checkpoints", [])

    def check_checkpoint(
        self, position: Tuple[float, float], checkpoint_idx: int
    ) -> bool:
        """
        特定のチェックポイントを通過したか判定

        Args:
            position: 車両の位置 (x, y)
            checkpoint_idx: チェックポイントのインデックス

        Returns:
            チェックポイントを通過したかどうか
        """
        checkpoints = self.get_checkpoints()
        if checkpoint_idx >= len(checkpoints):
            return False

        checkpoint = checkpoints[checkpoint_idx]
        cp_pos = checkpoint["position"]
        cp_radius = checkpoint.get("radius", 1.0)

        distance = np.sqrt(
            (position[0] - cp_pos[0]) ** 2 + (position[1] - cp_pos[1]) ** 2
        )
        return distance <= cp_radius

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        コースの境界を取得（描画用）

        Returns:
            (min_x, max_x, min_y, max_y)
        """
        all_vertices = []

        for wall_data in self.data.get("walls", []):
            if wall_data["type"] == "polygon":
                all_vertices.extend(wall_data["vertices"])
            elif wall_data["type"] == "box":
                center = wall_data["center"]
                w = wall_data["width"] / 2
                h = wall_data["height"] / 2
                all_vertices.extend(
                    [
                        [center[0] - w, center[1] - h],
                        [center[0] + w, center[1] + h],
                    ]
                )

        if not all_vertices:
            return (0, 10, 0, 10)

        xs = [v[0] for v in all_vertices]
        ys = [v[1] for v in all_vertices]

        return (min(xs), max(xs), min(ys), max(ys))
