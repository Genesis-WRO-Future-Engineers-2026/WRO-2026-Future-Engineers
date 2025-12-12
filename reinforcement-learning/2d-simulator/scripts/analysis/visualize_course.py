"""コースとチェックポイントを視覚化する診断ツール"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def visualize_course(course_file: str):
    """コース定義を視覚化"""

    with open(course_file, 'r') as f:
        course_data = json.load(f)

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # 壁の描画
    for wall in course_data['walls']:
        if wall['type'] == 'polygon':
            vertices = np.array(wall['vertices'])
            poly = patches.Polygon(vertices, closed=True,
                                   edgecolor='gray', facecolor='lightgray',
                                   linewidth=2, alpha=0.7)
            ax.add_patch(poly)

            # 壁の名前を表示
            if 'name' in wall:
                center = vertices.mean(axis=0)
                ax.text(center[0], center[1], wall['name'],
                       fontsize=8, ha='center', style='italic', color='darkgray')

    # スタート地点
    start = course_data['start_position']
    ax.plot(start[0], start[1], 'go', markersize=15, label='Start', zorder=10)
    ax.text(start[0], start[1] + 0.3, 'START', ha='center', fontsize=10,
           fontweight='bold', color='green')

    # ゴール地点
    goal = course_data['goal_position']
    goal_radius = course_data['goal_radius']
    goal_circle = patches.Circle(goal, goal_radius,
                                 edgecolor='gold', facecolor='yellow',
                                 linewidth=2, alpha=0.3, label='Goal')
    ax.add_patch(goal_circle)
    ax.plot(goal[0], goal[1], 'y*', markersize=20, zorder=10)
    ax.text(goal[0], goal[1] - goal_radius - 0.3, 'GOAL', ha='center',
           fontsize=10, fontweight='bold', color='orange')

    # チェックポイントの描画
    checkpoints = course_data['checkpoints']
    for i, cp in enumerate(checkpoints):
        pos = cp['position']
        radius = cp['radius']

        # チェックポイントの円
        cp_circle = patches.Circle(pos, radius,
                                   edgecolor='blue', facecolor='cyan',
                                   linewidth=2, alpha=0.3)
        ax.add_patch(cp_circle)

        # チェックポイント番号
        ax.plot(pos[0], pos[1], 'bo', markersize=10, zorder=10)
        ax.text(pos[0], pos[1], str(i), ha='center', va='center',
               fontsize=12, fontweight='bold', color='white')

        # ラベル
        ax.text(pos[0], pos[1] - radius - 0.2, f'CP{i}\nr={radius}',
               ha='center', fontsize=8, color='blue')

    # 想定ルートの描画（スタート→CP0→CP1→...→ゴール）
    route_points = [start]
    for cp in checkpoints:
        route_points.append(cp['position'])
    route_points.append(goal)

    route_points = np.array(route_points)
    ax.plot(route_points[:, 0], route_points[:, 1],
           'r--', linewidth=2, alpha=0.5, label='Expected Route', zorder=5)

    # 軸の設定
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    ax.set_xlabel('X (m)', fontsize=12)
    ax.set_ylabel('Y (m)', fontsize=12)
    ax.set_title(f"Course: {course_data['name']}\n{course_file}", fontsize=14)

    # コース情報の表示
    info_text = f"Start: ({start[0]:.2f}, {start[1]:.2f})\n"
    info_text += f"Goal: ({goal[0]:.2f}, {goal[1]:.2f})\n"
    info_text += f"Checkpoints: {len(checkpoints)}\n"
    info_text += f"Walls: {len(course_data['walls'])}"

    ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()

    # 保存
    output_file = course_file.replace('.json', '_visualization.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Visualization saved to: {output_file}")

    plt.show()

    # チェックポイント間の距離分析
    print("\n" + "=" * 60)
    print("Checkpoint Analysis:")
    print("=" * 60)

    for i in range(len(checkpoints)):
        cp = checkpoints[i]
        pos = np.array(cp['position'])

        if i == 0:
            prev_pos = np.array(start)
            print(f"Start → CP{i}: {np.linalg.norm(pos - prev_pos):.2f}m (radius={cp['radius']})")
        else:
            prev_pos = np.array(checkpoints[i-1]['position'])
            print(f"CP{i-1} → CP{i}: {np.linalg.norm(pos - prev_pos):.2f}m (radius={cp['radius']})")

    last_cp_pos = np.array(checkpoints[-1]['position'])
    goal_pos = np.array(goal)
    print(f"CP{len(checkpoints)-1} → Goal: {np.linalg.norm(goal_pos - last_cp_pos):.2f}m")

    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Visualize course and checkpoints")
    parser.add_argument("--course", type=str,
                       default="courses/real/real-course_course.json",
                       help="Path to course JSON file")
    args = parser.parse_args()

    visualize_course(args.course)
