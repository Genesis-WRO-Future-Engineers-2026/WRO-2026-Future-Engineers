"""チェックポイントが壁の内部にあるかチェック"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import numpy as np
from shapely.geometry import Point, Polygon

def point_in_polygon(point, vertices):
    """点がポリゴン内部にあるかチェック（Shapely使用）"""
    poly = Polygon(vertices)
    pt = Point(point)
    return poly.contains(pt)

def check_checkpoints_in_walls(course_file: str):
    """チェックポイントが壁の内部にないか確認"""

    with open(course_file, 'r') as f:
        course_data = json.load(f)

    print("=" * 70)
    print("Checkpoint Wall Collision Check")
    print("=" * 70)

    checkpoints = course_data['checkpoints']
    walls = course_data['walls']

    for i, cp in enumerate(checkpoints):
        pos = cp['position']
        radius = cp['radius']

        print(f"\nCP{i}: {pos}, radius={radius}")

        for wall in walls:
            if wall['type'] == 'polygon':
                vertices = wall['vertices']
                wall_name = wall.get('name', 'unnamed')

                # チェックポイント中心が壁の内部にあるか
                if point_in_polygon(pos, vertices):
                    print(f"  ❌ INSIDE {wall_name}!")

                # チェックポイントの半径を考慮した衝突チェック
                poly = Polygon(vertices)
                pt = Point(pos)
                distance = pt.distance(poly.exterior)

                if distance < radius:
                    print(f"  ⚠️  TOO CLOSE to {wall_name}: {distance:.2f}m < radius {radius}m")
                elif distance < radius + 0.5:  # 余裕0.5m
                    print(f"  ⚠️  Near {wall_name}: {distance:.2f}m (margin: {distance - radius:.2f}m)")

    print("\n" + "=" * 70)
    print("Recommended Safe Positions:")
    print("=" * 70)

    # 走行可能エリアの分析
    inner_wall = None
    outer_wall = None

    for wall in walls:
        if wall.get('name') == 'inner_wall_main':
            inner_wall = np.array(wall['vertices'])
        elif wall.get('name') == 'outer_wall':
            outer_wall = np.array(wall['vertices'])

    if inner_wall is not None and outer_wall is not None:
        print("\nコース構造分析:")
        print(f"outer_wall: X=[{outer_wall[:, 0].min():.2f}, {outer_wall[:, 0].max():.2f}], "
              f"Y=[{outer_wall[:, 1].min():.2f}, {outer_wall[:, 1].max():.2f}]")
        print(f"inner_wall: X=[{inner_wall[:, 0].min():.2f}, {inner_wall[:, 0].max():.2f}], "
              f"Y=[{inner_wall[:, 1].min():.2f}, {inner_wall[:, 1].max():.2f}]")

        print("\n推奨チェックポイント配置（走行可能エリア考慮）:")
        print("""
CP3: [9.0, 6.0] - 左上コーナー（inner_wallとouter_wallの間）
CP4: [11.5, 5.0] - 右上エリア（obstacle_1の上側）
CP5: [11.0, 1.5] - 右下エリア（outer_wallとobstacle_1の間）

または、obstacle_1を避けるルート:
CP3: [8.5, 6.0] - 左上
CP4: [8.5, 2.5] - 左下（obstacle_1の左側を通過）
CP5: [7.0, 1.5] - ゴール手前
        """)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--course", type=str,
                       default="courses/real/real-course_course.json")
    args = parser.parse_args()

    try:
        check_checkpoints_in_walls(args.course)
    except ImportError:
        print("⚠️  shapely not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "shapely"])
        print("✓ shapely installed. Please run again.")
