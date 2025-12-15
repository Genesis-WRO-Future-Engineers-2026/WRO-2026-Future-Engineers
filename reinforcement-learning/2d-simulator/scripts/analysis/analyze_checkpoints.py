"""チェックポイント配置の問題を診断"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import numpy as np

def analyze_checkpoints(course_file: str):
    """チェックポイントの配置を分析"""

    with open(course_file, 'r') as f:
        course_data = json.load(f)

    print("=" * 70)
    print(f"Course Analysis: {course_data['name']}")
    print("=" * 70)

    start = np.array(course_data['start_position'])
    goal = np.array(course_data['goal_position'])
    checkpoints = course_data['checkpoints']

    print(f"\nStart: {start} (angle={course_data['start_angle']:.2f} rad)")
    print(f"Goal: {goal} (radius={course_data['goal_radius']})")
    print(f"Total Checkpoints: {len(checkpoints)}\n")

    # チェックポイント情報
    print("Checkpoint Details:")
    print("-" * 70)
    for i, cp in enumerate(checkpoints):
        pos = np.array(cp['position'])
        radius = cp['radius']

        if i == 0:
            prev = start
            prev_name = "Start"
        else:
            prev = np.array(checkpoints[i-1]['position'])
            prev_name = f"CP{i-1}"

        distance = np.linalg.norm(pos - prev)
        print(f"CP{i}: pos={cp['position']}, radius={radius}")
        print(f"      {prev_name} → CP{i}: distance={distance:.2f}m")

    # 最後のチェックポイントからゴールまで
    last_cp = np.array(checkpoints[-1]['position'])
    goal_dist = np.linalg.norm(goal - last_cp)
    print(f"\nCP{len(checkpoints)-1} → Goal: distance={goal_dist:.2f}m")

    print("\n" + "=" * 70)
    print("Potential Issues:")
    print("=" * 70)

    # 問題1: チェックポイントが壁の中にある可能性
    print("\n1. Checkpoint Positions vs Walls:")
    for wall in course_data['walls']:
        if wall['type'] == 'polygon':
            vertices = np.array(wall['vertices'])
            print(f"\n   Wall: {wall.get('name', 'unnamed')}")
            print(f"   Bounds: X=[{vertices[:, 0].min():.2f}, {vertices[:, 0].max():.2f}], "
                  f"Y=[{vertices[:, 1].min():.2f}, {vertices[:, 1].max():.2f}]")

    # 問題2: チェックポイント間の距離が遠すぎる
    print("\n2. Distance Analysis:")
    all_distances = []
    for i in range(len(checkpoints)):
        if i == 0:
            prev = start
        else:
            prev = np.array(checkpoints[i-1]['position'])
        curr = np.array(checkpoints[i]['position'])
        dist = np.linalg.norm(curr - prev)
        all_distances.append(dist)

    print(f"   Min distance: {min(all_distances):.2f}m")
    print(f"   Max distance: {max(all_distances):.2f}m")
    print(f"   Avg distance: {np.mean(all_distances):.2f}m")

    # 距離が長すぎる区間
    for i, dist in enumerate(all_distances):
        if dist > 5.0:  # 5m以上離れている
            print(f"   ⚠️  CP{i-1 if i > 0 else 'Start'} → CP{i}: {dist:.2f}m (TOO FAR)")

    # 問題3: ショートカットの可能性
    print("\n3. Shortcut Analysis:")
    print("   Checking if direct path to later checkpoints is shorter...")

    for i in range(len(checkpoints) - 2):
        curr = np.array(checkpoints[i]['position'])
        next_cp = np.array(checkpoints[i+1]['position'])
        next_next_cp = np.array(checkpoints[i+2]['position'])

        normal_route = np.linalg.norm(next_cp - curr) + np.linalg.norm(next_next_cp - next_cp)
        shortcut = np.linalg.norm(next_next_cp - curr)

        if shortcut < normal_route * 0.8:  # ショートカットが20%以上短い
            saved = normal_route - shortcut
            print(f"   ⚠️  CP{i} → CP{i+2} shortcut saves {saved:.2f}m "
                  f"({saved/normal_route*100:.1f}% shorter)")
            print(f"       Normal: {normal_route:.2f}m, Shortcut: {shortcut:.2f}m")

    # 問題4: CP2の位置が問題ないか
    if len(checkpoints) >= 3:
        cp2 = np.array(checkpoints[2]['position'])
        print(f"\n4. CP2 Specific Analysis:")
        print(f"   CP2 position: {checkpoints[2]['position']}")
        print(f"   CP2 radius: {checkpoints[2]['radius']}")

        # CP1からCP2への経路を確認
        cp1 = np.array(checkpoints[1]['position'])
        cp1_to_cp2 = cp2 - cp1
        print(f"   CP1 → CP2 vector: [{cp1_to_cp2[0]:.2f}, {cp1_to_cp2[1]:.2f}]")
        print(f"   CP1 → CP2 distance: {np.linalg.norm(cp1_to_cp2):.2f}m")

        # CP0からCP2への直線距離
        cp0 = np.array(checkpoints[0]['position'])
        direct = np.linalg.norm(cp2 - cp0)
        via_cp1 = np.linalg.norm(cp1 - cp0) + np.linalg.norm(cp2 - cp1)
        print(f"   CP0 → CP2 direct: {direct:.2f}m")
        print(f"   CP0 → CP1 → CP2: {via_cp1:.2f}m")

        if direct < via_cp1 * 0.85:
            print(f"   ⚠️  エージェントがCP1をスキップしてCP2に直行する可能性あり！")

    print("\n" + "=" * 70)
    print("Recommendations:")
    print("=" * 70)
    print("""
1. CP2が壁の外側（コース外部）にある可能性
   → コース内部の走行経路上に配置すべき

2. チェックポイント間の距離が不均等
   → より均等に配置するか、中間チェックポイントを追加

3. ショートカットルートが存在
   → チェックポイント配置を調整して正規ルートを強制

4. CP2の半径が大きすぎる/小さすぎる
   → 半径0.7は適切だが、位置が問題の可能性
    """)

    print("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--course", type=str,
                       default="courses/real/real-course_course.json")
    args = parser.parse_args()

    analyze_checkpoints(args.course)
