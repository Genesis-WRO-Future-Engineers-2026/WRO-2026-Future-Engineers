"""S字カーブSVGをコースJSONに変換する簡易スクリプト"""
import json
import re
from xml.etree import ElementTree as ET

# SVGを読み込む
tree = ET.parse('courses/s-curve.svg')
root = tree.getroot()

# pathを探す
ns = {'svg': 'http://www.w3.org/2000/svg'}
path = root.find('.//{http://www.w3.org/2000/svg}path')

if path is None:
    # 名前空間なしで試す
    path = root.find('.//path')

if path is None:
    print("パスが見つかりません")
    print(f"ルート要素: {root.tag}")
    print(f"子要素: {[child.tag for child in root]}")
    exit(1)

d = path.get('d')
print(f"パスデータ: {d[:100]}...")

# 座標を抽出（簡易版 - V, C コマンドのみ対応）
tokens = re.findall(r'[MLHVCSQTAZ]|[-\d.]+', d)

vertices = []
current_x, current_y = 0.0, 0.0
i = 0

while i < len(tokens):
    cmd = tokens[i]

    if cmd == 'M':  # moveto
        i += 1
        x = float(tokens[i])
        i += 1
        y = float(tokens[i])
        current_x, current_y = x, y
        vertices.append([x, y])

    elif cmd == 'V':  # vertical lineto
        i += 1
        y = float(tokens[i])
        current_y = y
        vertices.append([current_x, current_y])

    elif cmd == 'C':  # cubic bezier
        # ベジェ曲線を細かく分割して滑らかなカーブを生成
        i += 1
        cp1x = float(tokens[i])
        i += 1
        cp1y = float(tokens[i])
        i += 1
        cp2x = float(tokens[i])
        i += 1
        cp2y = float(tokens[i])
        i += 1
        x = float(tokens[i])
        i += 1
        y = float(tokens[i])

        # ベジェ曲線を20分割して滑らかに
        num_segments = 20
        for j in range(1, num_segments + 1):
            t = j / num_segments
            # 3次ベジェ曲線の公式
            bx = (1-t)**3 * current_x + 3*(1-t)**2*t * cp1x + 3*(1-t)*t**2 * cp2x + t**3 * x
            by = (1-t)**3 * current_y + 3*(1-t)**2*t * cp1y + 3*(1-t)*t**2 * cp2y + t**3 * y
            vertices.append([bx, by])

        current_x, current_y = x, y

    elif cmd == 'Z':
        # パスを閉じる
        pass

    i += 1

print(f"抽出した頂点数: {len(vertices)}")
print(f"最初の5頂点: {vertices[:5]}")
print(f"最後の5頂点: {vertices[-5:]}")

# SVGの座標をシミュレーター座標系に変換（スケールと反転）
svg_width = 678
svg_height = 777
target_width = 10.0  # シミュレーターの幅

scale = target_width / svg_width

scaled_vertices = []
for x, y in vertices:
    # スケール調整 + Y軸反転（SVGは上が0、シミュレーターは下が0）
    new_x = x * scale
    new_y = (svg_height - y) * scale
    scaled_vertices.append([round(new_x, 2), round(new_y, 2)])

print(f"\nスケール後の最初の5頂点: {scaled_vertices[:5]}")
print(f"スケール後の最後の5頂点: {scaled_vertices[-5:]}")

# コースJSONを生成（外壁のみ）
course = {
    "name": "S-Curve Track",
    "description": "S字カーブのある難しいコース - 上級者向け",
    "difficulty": "hard",
    "start_position": [1.0, 5.0],  # 後で調整
    "start_angle": 0.0,
    "goal_position": [9.0, 5.0],  # 後で調整
    "goal_radius": 0.8,
    "walls": [
        {
            "type": "polygon",
            "name": "outer_wall",
            "vertices": scaled_vertices
        }
    ],
    "checkpoints": [
        {
            "position": [2.0, 5.0],
            "radius": 1.0,
            "index": 0
        },
        {
            "position": [5.0, 8.0],
            "radius": 1.0,
            "index": 1
        },
        {
            "position": [5.0, 3.0],
            "radius": 1.0,
            "index": 2
        },
        {
            "position": [8.0, 5.0],
            "radius": 1.0,
            "index": 3
        }
    ]
}

# 保存
output_file = "courses/curriculum/level4_s_curve_from_svg.json"
with open(output_file, 'w') as f:
    json.dump(course, f, indent=2)

print(f"\n✓ コースを保存しました: {output_file}")
print("\n注意: 外壁のみなので、内壁を追加する必要があります")
