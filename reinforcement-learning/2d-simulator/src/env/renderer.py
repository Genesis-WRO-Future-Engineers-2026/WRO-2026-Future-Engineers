"""Pygameによる描画"""

import pygame
import numpy as np
from typing import Tuple, List, Optional, TYPE_CHECKING
from Box2D import b2Vec2

# 循環インポートを防ぐため
if TYPE_CHECKING:
    from src.env.vehicle import Vehicle


class Renderer:
    """シミュレーションの可視化"""

    def __init__(
        self,
        screen_width: int = 800,
        screen_height: int = 600,
        pixels_per_meter: float = 50.0,
    ):
        """
        Args:
            screen_width: 画面幅 (px)
            screen_height: 画面高さ (px)
            pixels_per_meter: メートルあたりのピクセル数
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ppm = pixels_per_meter

        # Pygame初期化
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Minicar 2D Simulator")

        # クロック（フレームレート制御用）
        self.clock = pygame.time.Clock()
        self.fps = 30

        # フォント
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # カメラ設定
        self.camera_x = 0
        self.camera_y = 0

        # 色定義
        self.colors = {
            "background": (30, 30, 30),
            "wall": (100, 100, 100),
            "vehicle": (0, 150, 255),
            "lidar": (255, 255, 0),
            "checkpoint": (0, 255, 0),
            "goal": (255, 215, 0),
            "text": (255, 255, 255),
        }

    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """
        ワールド座標をスクリーン座標に変換

        Args:
            x, y: ワールド座標 (m)

        Returns:
            スクリーン座標 (px)
        """
        screen_x = int((x - self.camera_x) * self.ppm + self.screen_width / 2)
        screen_y = int(
            self.screen_height / 2 - (y - self.camera_y) * self.ppm
        )  # Y軸反転
        return screen_x, screen_y

    def set_camera(self, x: float, y: float):
        """
        カメラ位置を設定

        Args:
            x, y: カメラの中心座標 (m)
        """
        self.camera_x = x
        self.camera_y = y

    def clear(self):
        """画面をクリア"""
        self.screen.fill(self.colors["background"])

    def draw_walls(self, walls: List):
        """
        壁を描画

        Args:
            walls: Box2Dのbodyリスト
        """
        for wall in walls:
            # 壁の頂点を取得
            for fixture in wall.fixtures:
                shape = fixture.shape
                vertices = [
                    (wall.transform * v) for v in shape.vertices
                ]  # ワールド座標に変換

                # スクリーン座標に変換
                screen_vertices = [
                    self.world_to_screen(v.x, v.y) for v in vertices
                ]

                # ポリゴン描画
                if len(screen_vertices) >= 3:
                    pygame.draw.polygon(
                        self.screen, self.colors["wall"], screen_vertices
                    )
                    pygame.draw.polygon(
                        self.screen, (150, 150, 150), screen_vertices, 2
                    )  # 輪郭

    def draw_vehicle(self, vehicle: "Vehicle"):
        """
        車両を描画

        Args:
            vehicle: 描画する車両オブジェクト
        """
        # 車両の状態を取得
        state = vehicle.get_state()
        position = state["position"]
        angle = state["angle"]

        # 車両のサイズを取得（Vehicleオブジェクトから）
        length = vehicle.length
        width = vehicle.width

        # 車両の4隅の座標（ローカル座標）
        half_l = length / 2
        half_w = width / 2
        corners = [
            (half_l, half_w),
            (-half_l, half_w),
            (-half_l, -half_w),
            (half_l, -half_w),
        ]

        # 回転と平行移動
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        world_corners = []
        for lx, ly in corners:
            wx = position[0] + lx * cos_a - ly * sin_a
            wy = position[1] + lx * sin_a + ly * cos_a
            world_corners.append((wx, wy))

        # スクリーン座標に変換
        screen_corners = [self.world_to_screen(x, y) for x, y in world_corners]

        # 描画
        pygame.draw.polygon(self.screen, self.colors["vehicle"], screen_corners)
        pygame.draw.polygon(
            self.screen, (255, 255, 255), screen_corners, 2
        )  # 輪郭

        # 前方向を示す線
        front_x = position[0] + half_l * cos_a
        front_y = position[1] + half_l * sin_a
        center_screen = self.world_to_screen(position[0], position[1])
        front_screen = self.world_to_screen(front_x, front_y)
        pygame.draw.line(
            self.screen, (255, 0, 0), center_screen, front_screen, 3
        )

    def draw_lidar(
        self,
        position: Tuple[float, float],
        orientation: float,
        distances: np.ndarray,
        num_rays: int = 5,
        angle_min: float = 0.0,
        angle_max: float = 2 * np.pi,
    ):
        """
        LiDARスキャンを描画

        Args:
            position: センサー位置 (x, y) (m)
            orientation: センサーの向き (rad)
            distances: 距離データ
            num_rays: レイの本数
            angle_min: 最小角度 (rad)
            angle_max: 最大角度 (rad)
        """
        angles = np.linspace(angle_min, angle_max, num_rays, endpoint=True)
        center_screen = self.world_to_screen(position[0], position[1])

        for angle, distance in zip(angles, distances):
            absolute_angle = orientation + angle
            end_x = position[0] + distance * np.cos(absolute_angle)
            end_y = position[1] + distance * np.sin(absolute_angle)
            end_screen = self.world_to_screen(end_x, end_y)

            # LiDARのレイを描画（薄く）
            pygame.draw.line(
                self.screen, self.colors["lidar"], center_screen, end_screen, 1
            )

    def draw_checkpoint(self, position: Tuple[float, float], radius: float):
        """
        チェックポイントを描画

        Args:
            position: チェックポイント位置 (x, y) (m)
            radius: 半径 (m)
        """
        screen_pos = self.world_to_screen(position[0], position[1])
        screen_radius = int(radius * self.ppm)
        pygame.draw.circle(
            self.screen, self.colors["checkpoint"], screen_pos, screen_radius, 2
        )

    def draw_goal(self, position: Tuple[float, float], radius: float):
        """
        ゴールを描画

        Args:
            position: ゴール位置 (x, y) (m)
            radius: 半径 (m)
        """
        screen_pos = self.world_to_screen(position[0], position[1])
        screen_radius = int(radius * self.ppm)
        pygame.draw.circle(
            self.screen, self.colors["goal"], screen_pos, screen_radius, 3
        )
        # ゴールマークを描画
        pygame.draw.line(
            self.screen,
            self.colors["goal"],
            (screen_pos[0] - screen_radius, screen_pos[1]),
            (screen_pos[0] + screen_radius, screen_pos[1]),
            2,
        )
        pygame.draw.line(
            self.screen,
            self.colors["goal"],
            (screen_pos[0], screen_pos[1] - screen_radius),
            (screen_pos[0], screen_pos[1] + screen_radius),
            2,
        )

    def draw_text(self, text: str, x: int, y: int, color: Tuple[int, int, int] = None):
        """
        テキストを描画

        Args:
            text: 表示するテキスト
            x, y: スクリーン座標 (px)
            color: 色
        """
        if color is None:
            color = self.colors["text"]
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def draw_debug_info(self, info: dict):
        """
        デバッグ情報を描画

        Args:
            info: 表示する情報の辞書
        """
        y_offset = 10
        for key, value in info.items():
            if isinstance(value, float):
                text = f"{key}: {value:.2f}"
            else:
                text = f"{key}: {value}"
            self.draw_text(text, 10, y_offset)
            y_offset += 25

    def update(self):
        """画面を更新"""
        # イベント処理（ウィンドウの応答性を保つため）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # 終了要求

        pygame.display.flip()
        self.clock.tick(self.fps)  # フレームレート制限
        return True  # 継続

    def close(self):
        """Pygameを終了"""
        pygame.quit()
