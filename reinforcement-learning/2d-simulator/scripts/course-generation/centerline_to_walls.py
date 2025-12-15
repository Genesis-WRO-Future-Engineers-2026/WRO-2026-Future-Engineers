#!/usr/bin/env python3
"""
中心線SVGから外壁・内壁を生成

中心線のパスデータと幅情報から、Box2D用の外壁・内壁ポリゴンを生成する。

使用方法:
    python centerline_to_walls.py <svg_file> --width <width_in_meters> [options]
"""

import argparse
import json
import re
import sys
import math
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import List, Tuple


def split_path_by_moveto(d: str) -> List[str]:
    """
    SVGパスをMコマンドで分割

    Args:
        d: SVGパスのd属性文字列

    Returns:
        サブパスのリスト
    """
    # Mコマンドで分割（最初のMも含む）
    segments = re.split(r'(?=[Mm])', d.strip())
    # 空文字列を除外
    return [seg.strip() for seg in segments if seg.strip()]


def parse_svg_path_data(d: str) -> List[Tuple[float, float]]:
    """
    SVGパスデータ（d属性）から座標を抽出

    Args:
        d: SVGパスのd属性文字列

    Returns:
        座標のリスト [(x, y), ...]
    """
    vertices = []

    # コマンドと数値を分離（負の数も考慮）
    tokens = re.findall(r'[MLHVCSQTAZmlhvcsqtaz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', d)

    current_x, current_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    i = 0

    while i < len(tokens):
        cmd = tokens[i]

        if cmd in ['M', 'm']:  # moveto
            i += 1
            x = float(tokens[i])
            i += 1
            y = float(tokens[i])
            if cmd == 'm':  # relative
                x += current_x
                y += current_y
            current_x, current_y = x, y
            start_x, start_y = x, y
            vertices.append((x, y))

        elif cmd in ['L', 'l']:  # lineto
            i += 1
            x = float(tokens[i])
            i += 1
            y = float(tokens[i])
            if cmd == 'l':  # relative
                x += current_x
                y += current_y
            current_x, current_y = x, y
            vertices.append((x, y))

        elif cmd in ['H', 'h']:  # horizontal lineto
            i += 1
            x = float(tokens[i])
            if cmd == 'h':
                x += current_x
            current_x = x
            vertices.append((current_x, current_y))

        elif cmd in ['V', 'v']:  # vertical lineto
            i += 1
            y = float(tokens[i])
            if cmd == 'v':
                y += current_y
            current_y = y
            vertices.append((current_x, current_y))

        elif cmd in ['Z', 'z']:  # closepath
            # パスを閉じる（始点に戻る）
            current_x, current_y = start_x, start_y
            # 重複を避けるため、最初の点と異なる場合のみ追加
            if vertices[-1] != (start_x, start_y):
                vertices.append((start_x, start_y))

        else:
            # その他のコマンド（C, S, Q, T, A など）は未実装
            pass

        i += 1

    return vertices


def compute_perpendicular_offset(p1: Tuple[float, float],
                                 p2: Tuple[float, float],
                                 offset: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    線分p1-p2に対して、垂直方向にoffset離れた2点を計算

    Args:
        p1: 線分の始点 (x, y)
        p2: 線分の終点 (x, y)
        offset: オフセット距離（ピクセル単位）

    Returns:
        ((left_x, left_y), (right_x, right_y))
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy)

    if length < 1e-6:
        # 線分が極端に短い場合はオフセットなし
        return (p1, p1)

    # 単位ベクトル
    ux = dx / length
    uy = dy / length

    # 垂直ベクトル（左側: 90度回転）
    perp_x = -uy * offset
    perp_y = ux * offset

    # 左右の点
    left = (p1[0] + perp_x, p1[1] + perp_y)
    right = (p1[0] - perp_x, p1[1] - perp_y)

    return (left, right)


def generate_offset_polygon(centerline: List[Tuple[float, float]],
                            offset: float) -> List[Tuple[float, float]]:
    """
    中心線から、一定距離オフセットしたポリゴンを生成

    Args:
        centerline: 中心線の座標リスト [(x, y), ...]
        offset: オフセット距離（ピクセル単位）

    Returns:
        オフセットされたポリゴンの座標リスト
    """
    if len(centerline) < 2:
        return []

    offset_points = []

    for i in range(len(centerline) - 1):
        p1 = centerline[i]
        p2 = centerline[i + 1]

        left, _ = compute_perpendicular_offset(p1, p2, offset)
        offset_points.append(left)

    # 最後の点も追加
    if len(centerline) >= 2:
        p1 = centerline[-2]
        p2 = centerline[-1]
        left, _ = compute_perpendicular_offset(p2, p1, offset)  # 反転
        offset_points.append((p2[0] + (left[0] - p1[0]), p2[1] + (left[1] - p1[1])))

    return offset_points


def centerline_to_walls(centerline: List[Tuple[float, float]],
                       track_width_px: float) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    中心線から外壁・内壁を生成

    Args:
        centerline: 中心線の座標リスト [(x, y), ...]
        track_width_px: トラック幅（ピクセル単位）

    Returns:
        (outer_wall, inner_wall) のタプル
    """
    half_width = track_width_px / 2.0

    outer_wall = []
    inner_wall = []

    for i in range(len(centerline) - 1):
        p1 = centerline[i]
        p2 = centerline[i + 1]

        left, right = compute_perpendicular_offset(p1, p2, half_width)
        outer_wall.append(left)
        inner_wall.append(right)

    # 最後の点
    if len(centerline) >= 2:
        p1 = centerline[-2]
        p2 = centerline[-1]
        left, right = compute_perpendicular_offset(p2, p1, half_width)  # p2を基準にする
        outer_wall.append((p2[0] + (left[0] - p1[0]), p2[1] + (left[1] - p1[1])))
        inner_wall.append((p2[0] + (right[0] - p1[0]), p2[1] + (right[1] - p1[1])))

    return outer_wall, inner_wall


def svg_to_course(svg_file: str,
                 track_width_m: float,
                 scale: float = 0.001,
                 sim_scale: float = 10.0) -> dict:
    """
    SVGファイル（中心線）からコース定義JSONを生成

    Args:
        svg_file: SVGファイルのパス
        track_width_m: トラック幅（メートル単位）
        scale: px → m の変換係数（例: 0.001 = 1px = 1mm）
        sim_scale: m → シミュレーター単位（例: 10 = 1m = 10単位）

    Returns:
        コース定義辞書
    """
    print(f"📂 SVGファイルを読み込み中: {svg_file}")

    tree = ET.parse(svg_file)
    root = tree.getroot()

    # SVGの名前空間を取得
    ns_match = re.search(r'xmlns="([^"]+)"', ET.tostring(root, encoding='unicode'))

    # 名前空間あり・なし両方で検索を試みる
    if ns_match:
        ns = {'svg': ns_match.group(1)}
        paths = root.findall('.//svg:path', ns)
    else:
        paths = []

    # 名前空間なしでも試す
    if len(paths) == 0:
        paths = root.findall('.//path')

    # 名前空間付きで直接検索
    if len(paths) == 0:
        paths = root.findall('.//{http://www.w3.org/2000/svg}path')

    if len(paths) == 0:
        print("❌ エラー: SVGファイル内にパスが見つかりません")
        sys.exit(1)

    print(f"✓ {len(paths)}個のパス要素を検出")

    # すべてのパスを解析し、サブパスに分割して最も長いものを選択
    longest_vertices = []
    all_subpaths = []

    for i, path_elem in enumerate(paths):
        d = path_elem.get('d')
        if not d:
            continue

        # サブパスに分割
        subpaths = split_path_by_moveto(d)
        print(f"  パス#{i}: {len(subpaths)}個のサブパスを検出")

        for j, subpath_d in enumerate(subpaths):
            vertices = parse_svg_path_data(subpath_d)
            if len(vertices) >= 3:  # 最低3頂点
                all_subpaths.append((vertices, f"パス#{i}-サブパス#{j}"))
                print(f"    サブパス#{j}: {len(vertices)} 頂点")

                if len(vertices) > len(longest_vertices):
                    longest_vertices = vertices

    if len(longest_vertices) < 3:
        print("❌ エラー: 有効なパスが見つかりません")
        sys.exit(1)

    print(f"✓ 最も長いサブパス（{len(longest_vertices)} 頂点）を中心線として使用")

    centerline_px = longest_vertices

    # トラック幅をピクセル単位に変換
    track_width_px = track_width_m / scale

    print(f"✓ 外壁・内壁を生成中...")
    print(f"  トラック幅: {track_width_m}m = {track_width_px}px")

    # 外壁・内壁を生成
    outer_wall_px, inner_wall_px = centerline_to_walls(centerline_px, track_width_px)

    print(f"  外壁の頂点数: {len(outer_wall_px)}")
    print(f"  内壁の頂点数: {len(inner_wall_px)}")

    # シミュレーター座標系に変換
    def convert_to_sim(vertices_px):
        vertices = []
        for x, y in vertices_px:
            x_sim = x * scale * sim_scale
            y_sim = y * scale * sim_scale
            vertices.append([round(x_sim, 2), round(y_sim, 2)])
        return vertices

    outer_wall_sim = convert_to_sim(outer_wall_px)
    inner_wall_sim = convert_to_sim(inner_wall_px)

    # コース定義を構築
    course = {
        "name": f"Real Course (Width: {track_width_m}m)",
        "description": f"中心線SVGから生成 (トラック幅: {track_width_m}m)",
        "difficulty": "hard",
        "start_position": [3.0, 1.5],  # TODO: 調整が必要
        "start_angle": 0.0,
        "goal_position": [3.0, 1.5],  # TODO: 調整が必要
        "goal_radius": 1.0,
        "walls": [
            {
                "type": "polygon",
                "name": "outer_wall",
                "vertices": outer_wall_sim
            },
            {
                "type": "polygon",
                "name": "inner_wall",
                "vertices": inner_wall_sim
            }
        ],
        "checkpoints": []  # TODO: 後で追加
    }

    return course


def main():
    parser = argparse.ArgumentParser(
        description="中心線SVGから外壁・内壁を生成してコース定義JSONを作成"
    )
    parser.add_argument("svg_file", help="入力SVGファイルのパス（中心線）")
    parser.add_argument(
        "-w", "--width",
        type=float,
        required=True,
        help="トラック幅（メートル単位、例: 0.9）"
    )
    parser.add_argument(
        "-o", "--output",
        help="出力JSONファイルのパス（デフォルト: courses/real/<svg名>_w<幅>m.json）"
    )
    parser.add_argument(
        "-s", "--scale",
        type=float,
        default=0.001,
        help="px→m変換係数（デフォルト: 0.001 = 1px=1mm）"
    )
    parser.add_argument(
        "--sim-scale",
        type=float,
        default=10.0,
        help="m→シミュレーター単位（デフォルト: 10 = 1m=10単位）"
    )

    args = parser.parse_args()

    # 入力ファイルの確認
    svg_path = Path(args.svg_file)
    if not svg_path.exists():
        print(f"❌ エラー: ファイルが見つかりません: {svg_path}")
        sys.exit(1)

    # 出力ファイル名の決定
    if args.output:
        output_path = Path(args.output)
    else:
        width_str = str(args.width).replace('.', '_')
        output_path = Path("courses/real") / f"{svg_path.stem}_w{width_str}m.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🎨 中心線SVG → 外壁・内壁JSON 変換")
    print("=" * 60)
    print(f"入力: {svg_path}")
    print(f"出力: {output_path}")
    print(f"トラック幅: {args.width}m")
    print(f"スケール: 1px = {args.scale}m, 1m = {args.sim_scale}単位")
    print("=" * 60)

    try:
        # SVGからコース定義を生成
        course = svg_to_course(
            str(svg_path),
            args.width,
            args.scale,
            args.sim_scale
        )

        # JSONとして保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(course, f, indent=2, ensure_ascii=False)

        print("=" * 60)
        print(f"✅ 変換完了: {output_path}")
        print(f"   壁の数: {len(course['walls'])}")
        for wall in course['walls']:
            print(f"   - {wall['name']}: {len(wall['vertices'])} 頂点")
        print("=" * 60)
        print("\n次のステップ:")
        print("1. JSONを編集してスタート/ゴール位置を調整")
        print("2. チェックポイントを追加")
        print("3. GUIで確認:")
        print(f"   python scripts/rl-training/train.py --course {output_path} --gui")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
