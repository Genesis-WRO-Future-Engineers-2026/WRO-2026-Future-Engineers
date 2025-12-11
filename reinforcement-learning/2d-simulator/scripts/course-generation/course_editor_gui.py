#!/usr/bin/env python3
"""
コース定義JSONを対話的に編集するGUIツール

使用方法:
    python course_editor_gui.py <json_file>

機能:
    - 壁の頂点を視覚的に編集（ドラッグ＆ドロップ）
    - 頂点の追加・削除
    - スタート/ゴール/チェックポイントの配置
    - リアルタイムプレビュー
    - Undo/Redo

依存パッケージ:
    pip install pygame numpy
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np

try:
    import pygame
except ImportError:
    print("エラー: pygameがインストールされていません")
    print("pip install pygame")
    sys.exit(1)


class CourseEditor:
    """コース編集用GUIエディタ"""

    def __init__(self, json_path: str, window_size: Tuple[int, int] = (1400, 900)):
        """
        Args:
            json_path: 編集するJSONファイルのパス
            window_size: ウィンドウサイズ
        """
        self.json_path = Path(json_path)
        self.course_data = self.load_course(self.json_path)

        # Pygame初期化
        pygame.init()
        self.screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption(f"Course Editor - {self.json_path.name}")

        self.width, self.height = window_size
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.small_font = pygame.font.SysFont("Arial", 12)

        # 編集状態
        self.selected_wall_idx = 0
        self.selected_vertex_idx = None
        self.dragging = False
        self.drag_offset = (0, 0)

        # 表示設定
        self.offset = [50, 50]
        self.zoom = 1.0
        self.show_grid = True
        self.show_vertices = True

        # 編集モード
        self.mode = "edit"  # "edit", "add_vertex", "delete_vertex", "add_checkpoint"

        # Undo/Redo
        self.history = [json.dumps(self.course_data)]
        self.history_index = 0

        # 色設定
        self.colors = {
            "background": (240, 240, 245),
            "grid": (220, 220, 225),
            "wall": (60, 60, 80),
            "wall_selected": (100, 150, 255),
            "vertex": (255, 100, 100),
            "vertex_hover": (255, 150, 50),
            "start": (50, 200, 50),
            "goal": (200, 50, 50),
            "checkpoint": (255, 200, 50),
            "text": (50, 50, 50),
        }

    def load_course(self, path: Path) -> dict:
        """JSONファイルからコース定義を読み込み"""
        if not path.exists():
            # 新規作成
            return {
                "name": "New Course",
                "description": "",
                "difficulty": "medium",
                "start_position": [5.0, 5.0],
                "start_angle": 0.0,
                "goal_position": [5.0, 5.0],
                "goal_radius": 1.0,
                "walls": [],
                "checkpoints": [],
            }

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_course(self):
        """JSONファイルに保存"""
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.course_data, f, indent=2, ensure_ascii=False)
        print(f"✓ 保存しました: {self.json_path}")

    def save_to_history(self):
        """現在の状態を履歴に保存"""
        # 現在位置以降の履歴を削除
        self.history = self.history[: self.history_index + 1]
        # 新しい状態を追加
        self.history.append(json.dumps(self.course_data))
        self.history_index += 1
        # 履歴を50件に制限
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self):
        """元に戻す"""
        if self.history_index > 0:
            self.history_index -= 1
            self.course_data = json.loads(self.history[self.history_index])
            print("Undo")

    def redo(self):
        """やり直し"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.course_data = json.loads(self.history[self.history_index])
            print("Redo")

    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """ワールド座標をスクリーン座標に変換"""
        screen_x = int((x * self.zoom) + self.offset[0])
        screen_y = int(self.height - ((y * self.zoom) + self.offset[1]))
        return screen_x, screen_y

    def screen_to_world(self, x: int, y: int) -> Tuple[float, float]:
        """スクリーン座標をワールド座標に変換"""
        world_x = (x - self.offset[0]) / self.zoom
        world_y = (self.height - y - self.offset[1]) / self.zoom
        return world_x, world_y

    def draw_grid(self):
        """グリッドを描画"""
        if not self.show_grid:
            return

        grid_size = 5.0  # ワールド座標で5単位ごと
        screen_grid = int(grid_size * self.zoom)

        # 垂直線
        x = self.offset[0] % screen_grid
        while x < self.width:
            pygame.draw.line(
                self.screen, self.colors["grid"], (x, 0), (x, self.height), 1
            )
            x += screen_grid

        # 水平線
        y = self.offset[1] % screen_grid
        while y < self.height:
            pygame.draw.line(
                self.screen, self.colors["grid"], (0, self.height - y), (self.width, self.height - y), 1
            )
            y += screen_grid

    def draw_walls(self):
        """壁を描画"""
        walls = self.course_data.get("walls", [])

        for wall_idx, wall in enumerate(walls):
            vertices = wall.get("vertices", [])
            if len(vertices) < 2:
                continue

            # 色を選択（選択中かどうか）
            color = (
                self.colors["wall_selected"]
                if wall_idx == self.selected_wall_idx
                else self.colors["wall"]
            )

            # ポリゴンを描画
            screen_points = [self.world_to_screen(v[0], v[1]) for v in vertices]
            if len(screen_points) >= 3:
                pygame.draw.polygon(self.screen, color, screen_points, 2)

            # 頂点を描画
            if self.show_vertices and wall_idx == self.selected_wall_idx:
                for vertex_idx, (x, y) in enumerate(vertices):
                    sx, sy = self.world_to_screen(x, y)

                    # ホバー検出
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    dist = ((sx - mouse_x) ** 2 + (sy - mouse_y) ** 2) ** 0.5

                    vertex_color = (
                        self.colors["vertex_hover"]
                        if dist < 8
                        else self.colors["vertex"]
                    )
                    radius = 6 if dist < 8 else 4

                    pygame.draw.circle(self.screen, vertex_color, (sx, sy), radius)

                    # 頂点番号を表示
                    text = self.small_font.render(str(vertex_idx), True, self.colors["text"])
                    self.screen.blit(text, (sx + 8, sy - 8))

    def draw_markers(self):
        """スタート/ゴール/チェックポイントを描画"""
        # スタート
        start = self.course_data.get("start_position", [0, 0])
        sx, sy = self.world_to_screen(start[0], start[1])
        pygame.draw.circle(self.screen, self.colors["start"], (sx, sy), 8)
        pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), 8, 2)
        text = self.font.render("START", True, self.colors["start"])
        self.screen.blit(text, (sx + 12, sy - 8))

        # ゴール
        goal = self.course_data.get("goal_position", [0, 0])
        goal_radius = self.course_data.get("goal_radius", 1.0)
        gx, gy = self.world_to_screen(goal[0], goal[1])
        gr = int(goal_radius * self.zoom)
        pygame.draw.circle(self.screen, self.colors["goal"], (gx, gy), gr, 2)
        pygame.draw.circle(self.screen, self.colors["goal"], (gx, gy), 8)
        text = self.font.render("GOAL", True, self.colors["goal"])
        self.screen.blit(text, (gx + 12, gy - 8))

        # チェックポイント
        for i, cp in enumerate(self.course_data.get("checkpoints", [])):
            pos = cp.get("position", [0, 0])
            radius = cp.get("radius", 1.0)
            cx, cy = self.world_to_screen(pos[0], pos[1])
            cr = int(radius * self.zoom)
            pygame.draw.circle(self.screen, self.colors["checkpoint"], (cx, cy), cr, 2)
            pygame.draw.circle(self.screen, self.colors["checkpoint"], (cx, cy), 6)
            text = self.small_font.render(f"CP{i}", True, self.colors["checkpoint"])
            self.screen.blit(text, (cx + 10, cy - 6))

    def draw_ui(self):
        """UI要素を描画"""
        # 背景パネル
        panel_rect = pygame.Rect(10, 10, 300, 200)
        pygame.draw.rect(self.screen, (50, 50, 50, 180), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, 2)

        y_offset = 20
        line_height = 20

        # タイトル
        text = self.font.render("Course Editor", True, (255, 255, 255))
        self.screen.blit(text, (20, y_offset))
        y_offset += line_height * 1.5

        # 情報表示
        info_lines = [
            f"Mode: {self.mode}",
            f"Wall: {self.selected_wall_idx + 1}/{len(self.course_data.get('walls', []))}",
            f"Zoom: {self.zoom:.1f}x",
            f"",
            "[操作]",
            "左クリック: 頂点を移動",
            "右クリック: 壁を選択",
            "A: 頂点追加モード",
            "D: 頂点削除モード",
            "S: 保存",
            "Z: Undo / Y: Redo",
            "G: グリッド表示",
        ]

        for line in info_lines:
            text = self.small_font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (20, y_offset))
            y_offset += line_height

    def find_vertex_at_pos(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """指定位置にある頂点を検索"""
        walls = self.course_data.get("walls", [])
        if self.selected_wall_idx >= len(walls):
            return None

        vertices = walls[self.selected_wall_idx].get("vertices", [])

        for vertex_idx, (vx, vy) in enumerate(vertices):
            sx, sy = self.world_to_screen(vx, vy)
            dist = ((sx - x) ** 2 + (sy - y) ** 2) ** 0.5
            if dist < 8:
                return (self.selected_wall_idx, vertex_idx)

        return None

    def handle_events(self):
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    # 保存
                    self.save_course()

                elif event.key == pygame.K_z:
                    # Undo
                    self.undo()

                elif event.key == pygame.K_y:
                    # Redo
                    self.redo()

                elif event.key == pygame.K_g:
                    # グリッド表示切り替え
                    self.show_grid = not self.show_grid

                elif event.key == pygame.K_a:
                    # 頂点追加モード
                    self.mode = "add_vertex"
                    print("モード: 頂点追加（クリックして頂点を追加）")

                elif event.key == pygame.K_d:
                    # 頂点削除モード
                    self.mode = "delete_vertex"
                    print("モード: 頂点削除（頂点をクリックして削除）")

                elif event.key == pygame.K_ESCAPE:
                    # 編集モードに戻る
                    self.mode = "edit"
                    print("モード: 編集")

                elif event.key == pygame.K_LEFT:
                    # 前の壁を選択
                    if self.selected_wall_idx > 0:
                        self.selected_wall_idx -= 1

                elif event.key == pygame.K_RIGHT:
                    # 次の壁を選択
                    walls = self.course_data.get("walls", [])
                    if self.selected_wall_idx < len(walls) - 1:
                        self.selected_wall_idx += 1

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    self.handle_left_click(event.pos)

                elif event.button == 3:  # 右クリック
                    self.handle_right_click(event.pos)

                elif event.button == 4:  # ホイール上
                    self.zoom *= 1.1

                elif event.button == 5:  # ホイール下
                    self.zoom /= 1.1

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.dragging:
                        self.dragging = False
                        self.save_to_history()

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging and self.selected_vertex_idx is not None:
                    # 頂点をドラッグ
                    wx, wy = self.screen_to_world(event.pos[0], event.pos[1])
                    walls = self.course_data.get("walls", [])
                    wall_idx, vertex_idx = self.selected_vertex_idx
                    walls[wall_idx]["vertices"][vertex_idx] = [
                        round(wx, 2),
                        round(wy, 2),
                    ]

        return True

    def handle_left_click(self, pos: Tuple[int, int]):
        """左クリック処理"""
        if self.mode == "edit":
            # 頂点をドラッグ開始
            result = self.find_vertex_at_pos(pos[0], pos[1])
            if result:
                self.selected_vertex_idx = result
                self.dragging = True

        elif self.mode == "add_vertex":
            # 頂点を追加
            wx, wy = self.screen_to_world(pos[0], pos[1])
            walls = self.course_data.get("walls", [])
            if self.selected_wall_idx < len(walls):
                walls[self.selected_wall_idx]["vertices"].append([round(wx, 2), round(wy, 2)])
                self.save_to_history()
                print(f"頂点を追加: ({wx:.2f}, {wy:.2f})")

        elif self.mode == "delete_vertex":
            # 頂点を削除
            result = self.find_vertex_at_pos(pos[0], pos[1])
            if result:
                wall_idx, vertex_idx = result
                walls = self.course_data.get("walls", [])
                del walls[wall_idx]["vertices"][vertex_idx]
                self.save_to_history()
                print(f"頂点を削除: #{vertex_idx}")

    def handle_right_click(self, pos: Tuple[int, int]):
        """右クリック処理（壁の選択）"""
        # TODO: クリック位置に最も近い壁を選択
        pass

    def run(self):
        """メインループ"""
        running = True
        while running:
            self.screen.fill(self.colors["background"])

            # グリッドを描画
            self.draw_grid()

            # コースを描画
            self.draw_walls()
            self.draw_markers()

            # UIを描画
            self.draw_ui()

            # イベント処理
            running = self.handle_events()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="コース定義JSONを対話的に編集")
    parser.add_argument("json_file", help="編集するJSONファイルのパス")
    parser.add_argument(
        "--width", type=int, default=1400, help="ウィンドウ幅（デフォルト: 1400）"
    )
    parser.add_argument(
        "--height", type=int, default=900, help="ウィンドウ高さ（デフォルト: 900）"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🎨 Course Editor")
    print("=" * 60)
    print(f"ファイル: {args.json_file}")
    print("\n[操作方法]")
    print("  左クリック: 頂点を移動")
    print("  右クリック: 壁を選択")
    print("  A: 頂点追加モード")
    print("  D: 頂点削除モード")
    print("  S: 保存")
    print("  Z: Undo / Y: Redo")
    print("  G: グリッド表示切り替え")
    print("  ←/→: 壁を切り替え")
    print("  ESC: 編集モードに戻る")
    print("  マウスホイール: ズーム")
    print("=" * 60)

    editor = CourseEditor(args.json_file, (args.width, args.height))
    editor.run()


if __name__ == "__main__":
    main()
