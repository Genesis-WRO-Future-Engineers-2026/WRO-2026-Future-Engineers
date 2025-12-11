#!/usr/bin/env python3
"""
コース幅情報付きSVGファイルをコース定義JSONに変換

SVGファイルに含まれるコースパス（中心線）とコース幅テキストから、
内周・外周の壁を自動生成する。

使用方法:
    python svg_with_width_to_course.py <svg_file> [options]

依存パッケージ:
    標準ライブラリのみ（追加インストール不要）
"""

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import List, Tuple, Dict
import math


def parse_svg_path_data(d: str) -> List[Tuple[float, float]]:
    """
    SVGパスデータ（d属性）から座標を抽出

    Args:
        d: SVGパスのd属性文字列

    Returns:
        座標のリスト [(x, y), ...]
    """
    vertices = []

    # コマンドと数値を分離
    tokens = re.findall(r'[MLHVCSQTAZmlhvcsqtaz]|[-\d.]+', d)

    current_x, current_y = 0.0, 0.0
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

        elif cmd in ['C', 'c']:  # curveto (cubic bezier)
            # ベジェ曲線は終点のみを使用（簡易実装）
            i += 1
            _ = float(tokens[i])  # 制御点1 x
            i += 1
            _ = float(tokens[i])  # 制御点1 y
            i += 1
            _ = float(tokens[i])  # 制御点2 x
            i += 1
            _ = float(tokens[i])  # 制御点2 y
            i += 1
            x = float(tokens[i])  # 終点 x
            i += 1
            y = float(tokens[i])  # 終点 y
            if cmd == 'c':
                x += current_x
                y += current_y
            current_x, current_y = x, y
            vertices.append((x, y))

        elif cmd in ['Z', 'z']:  # closepath
            # 最初の点に戻る
            if vertices:
                current_x, current_y = vertices[0]

        i += 1

    return vertices


def extract_width_annotations(root: ET.Element) -> Dict[Tuple[float, float], float]:
    """
    SVGからコース幅のテキストアノテーションを抽出

    Args:
        root: SVGのルート要素

    Returns:
        {(x, y): width_in_meters} の辞書
    """
    width_annotations = {}

    # <text>要素を検索（名前空間を考慮）
    # 名前空間ありで検索
    ns_match = re.search(r'xmlns="([^"]+)"', ET.tostring(root, encoding='unicode'))
    ns = {'svg': ns_match.group(1)} if ns_match else {}

    text_elements = root.findall('.//svg:text', ns) if ns else root.findall('.//text')
    if not text_elements:
        text_elements = root.findall('.//{http://www.w3.org/2000/svg}text')
    if not text_elements:
        # 名前空間なしでも試す
        text_elements = [elem for elem in root.iter() if elem.tag.endswith('text')]

    print(f"  {len(text_elements)} 個のtext要素を検出しました")

    for text_elem in text_elements:
        x = float(text_elem.get('x', 0))
        y = float(text_elem.get('y', 0))
        text_content = text_elem.text

        if text_content:
            # "1.22m" のような形式から数値を抽出
            match = re.search(r'([\d.]+)\s*m', text_content)
            if match:
                width = float(match.group(1))
                width_annotations[(x, y)] = width
                print(f"  幅アノテーション検出: ({x:.0f}, {y:.0f}) → {width}m")

    return width_annotations


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """2点間の距離を計算"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def find_nearest_width(point: Tuple[float, float],
                       width_annotations: Dict[Tuple[float, float], float],
                       default_width: float = 1.0) -> float:
    """
    指定された点に最も近い幅アノテーションを見つける

    Args:
        point: 対象の点
        width_annotations: 幅アノテーションの辞書
        default_width: デフォルト幅（m）

    Returns:
        幅（m）
    """
    if not width_annotations:
        return default_width

    min_dist = float('inf')
    nearest_width = default_width

    for anno_point, width in width_annotations.items():
        dist = distance(point, anno_point)
        if dist < min_dist:
            min_dist = dist
            nearest_width = width

    return nearest_width


def interpolate_widths(centerline: List[Tuple[float, float]],
                       width_annotations: Dict[Tuple[float, float], float],
                       default_width: float = 1.0) -> List[float]:
    """
    中心線の各点に対する幅を補間

    Args:
        centerline: 中心線の座標リスト
        width_annotations: 幅アノテーションの辞書
        default_width: デフォルト幅（m）

    Returns:
        各点の幅リスト
    """
    widths = []

    for point in centerline:
        width = find_nearest_width(point, width_annotations, default_width)
        widths.append(width)

    return widths


def calculate_normal(p1: Tuple[float, float],
                     p2: Tuple[float, float]) -> Tuple[float, float]:
    """
    2点間のセグメントに対する法線ベクトル（正規化済み）を計算

    Args:
        p1: 始点
        p2: 終点

    Returns:
        正規化された法線ベクトル (nx, ny)
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx**2 + dy**2)

    if length < 1e-6:
        return (0.0, 0.0)

    # 法線ベクトル（90度回転）
    nx = -dy / length
    ny = dx / length

    return (nx, ny)


def generate_offset_path(centerline: List[Tuple[float, float]],
                         widths: List[float],
                         offset_side: float,
                         scale: float,
                         sim_scale: float) -> List[List[float]]:
    """
    中心線から指定された側にオフセットしたパスを生成

    Args:
        centerline: 中心線の座標リスト
        widths: 各点の幅リスト（m）
        offset_side: オフセット方向（+0.5=右側、-0.5=左側）
        scale: px → m の変換係数
        sim_scale: m → シミュレーター単位

    Returns:
        オフセットされた座標リスト [[x, y], ...]
    """
    offset_path = []
    n = len(centerline)

    for i in range(n):
        # 現在の点
        current = centerline[i]

        # 法線ベクトルを計算（前後のセグメントの平均）
        if i == 0:
            # 最初の点: 次のセグメントの法線のみ
            normal = calculate_normal(centerline[i], centerline[i + 1])
        elif i == n - 1:
            # 最後の点: 前のセグメントの法線のみ
            normal = calculate_normal(centerline[i - 1], centerline[i])
        else:
            # 中間の点: 前後のセグメントの法線の平均
            n1 = calculate_normal(centerline[i - 1], centerline[i])
            n2 = calculate_normal(centerline[i], centerline[i + 1])
            normal = ((n1[0] + n2[0]) / 2, (n1[1] + n2[1]) / 2)
            # 正規化
            length = math.sqrt(normal[0]**2 + normal[1]**2)
            if length > 1e-6:
                normal = (normal[0] / length, normal[1] / length)

        # オフセット距離（ピクセル単位）
        offset_dist = widths[i] * offset_side / scale

        # オフセットされた点
        offset_x = current[0] + normal[0] * offset_dist
        offset_y = current[1] + normal[1] * offset_dist

        # スケール変換
        x_sim = offset_x * scale * sim_scale
        y_sim = offset_y * scale * sim_scale

        offset_path.append([round(x_sim, 2), round(y_sim, 2)])

    return offset_path


def svg_to_course_with_width(svg_file: str,
                              scale: float = 0.001,
                              sim_scale: float = 10.0,
                              default_width: float = 1.0) -> dict:
    """
    コース幅情報付きSVGファイルからコース定義JSONを生成

    Args:
        svg_file: SVGファイルのパス
        scale: px → m の変換係数（例: 0.001 = 1px = 1mm）
        sim_scale: m → シミュレーター単位（例: 10 = 1m = 10単位）
        default_width: デフォルトのコース幅（m）

    Returns:
        コース定義辞書
    """
    print(f"📂 SVGファイルを読み込み中: {svg_file}")

    tree = ET.parse(svg_file)
    root = tree.getroot()

    # 名前空間を処理
    # SVGの名前空間を取得
    ns_match = re.search(r'xmlns="([^"]+)"', ET.tostring(root, encoding='unicode'))
    ns = {'svg': ns_match.group(1)} if ns_match else {}

    # 幅アノテーションを抽出
    print("\n幅アノテーションを抽出中...")
    width_annotations = extract_width_annotations(root)

    if not width_annotations:
        print("  警告: 幅アノテーションが見つかりません。デフォルト幅を使用します。")

    # パス要素を検索（stroke属性を持つpathをコース中心線として使用）
    # 名前空間ありとなしの両方を試す
    paths = root.findall('.//svg:path', ns) if ns else root.findall('.//path')
    if not paths:
        paths = root.findall('.//{http://www.w3.org/2000/svg}path')
    if not paths:
        # 名前空間なしでも試す
        paths = [elem for elem in root.iter() if elem.tag.endswith('path')]

    if len(paths) == 0:
        print("エラー: SVGファイル内にパスが見つかりません")
        sys.exit(1)

    print(f"\n{len(paths)} 個のパス要素を検出しました")

    # stroke属性を持つパスを中心線として使用（テキストパスはfill属性のみ）
    centerline_path = None
    for i, path in enumerate(paths):
        stroke = path.get('stroke')
        fill = path.get('fill')
        print(f"  パス#{i}: stroke={stroke}, fill={fill}")
        if stroke:
            centerline_path = path
            print(f"  → このパスをコース中心線として使用します")
            break

    if centerline_path is None:
        print("エラー: コース中心線（stroke属性を持つpath）が見つかりません")
        sys.exit(1)

    d = centerline_path.get('d')

    if not d:
        print("エラー: パスにd属性がありません")
        sys.exit(1)

    # 中心線の座標を抽出
    print("\nコース中心線を解析中...")
    centerline = parse_svg_path_data(d)
    print(f"  中心線の頂点数: {len(centerline)}")

    # 各点の幅を補間
    print("\nコース幅を補間中...")
    widths = interpolate_widths(centerline, width_annotations, default_width)

    avg_width = sum(widths) / len(widths) if widths else default_width
    min_width = min(widths) if widths else default_width
    max_width = max(widths) if widths else default_width
    print(f"  平均幅: {avg_width:.2f}m")
    print(f"  最小幅: {min_width:.2f}m")
    print(f"  最大幅: {max_width:.2f}m")

    # 内周・外周を生成
    print("\n内周・外周を生成中...")
    inner_wall = generate_offset_path(centerline, widths, -0.5, scale, sim_scale)
    outer_wall = generate_offset_path(centerline, widths, +0.5, scale, sim_scale)

    print(f"  内周: {len(inner_wall)} 頂点")
    print(f"  外周: {len(outer_wall)} 頂点")

    # 中心線の座標もスケール変換
    centerline_sim = []
    for x, y in centerline:
        x_sim = x * scale * sim_scale
        y_sim = y * scale * sim_scale
        centerline_sim.append([round(x_sim, 2), round(y_sim, 2)])

    # スタート位置とゴール位置を中心線の最初と最後の点に設定
    start_position = centerline_sim[0] if centerline_sim else [0.0, 0.0]
    goal_position = centerline_sim[-1] if centerline_sim else [0.0, 0.0]

    # コース定義を構築
    course = {
        "name": "Real Course - With Variable Width",
        "description": "SVGから自動生成（可変幅対応）",
        "difficulty": "hard",
        "start_position": start_position,
        "start_angle": 0.0,
        "goal_position": goal_position,
        "goal_radius": 1.0,
        "walls": [
            {
                "type": "polygon",
                "name": "outer_wall",
                "vertices": outer_wall
            },
            {
                "type": "polygon",
                "name": "inner_wall",
                "vertices": inner_wall
            }
        ],
        "checkpoints": []
    }

    return course


def main():
    parser = argparse.ArgumentParser(
        description="コース幅情報付きSVGファイルからコース定義JSONを生成"
    )
    parser.add_argument("svg_file", help="入力SVGファイルのパス")
    parser.add_argument(
        "-o", "--output",
        help="出力JSONファイルのパス（デフォルト: courses/real/<svg名>_course.json）"
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
    parser.add_argument(
        "--default-width",
        type=float,
        default=1.0,
        help="デフォルトのコース幅（m）（デフォルト: 1.0）"
    )

    args = parser.parse_args()

    # 入力ファイルの確認
    svg_path = Path(args.svg_file)
    if not svg_path.exists():
        print(f"エラー: ファイルが見つかりません: {svg_path}")
        sys.exit(1)

    # 出力ファイル名の決定
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path("courses/real") / f"{svg_path.stem}_course.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🎨 SVG → JSON 変換（可変幅対応）")
    print("=" * 60)
    print(f"入力: {svg_path}")
    print(f"出力: {output_path}")
    print(f"スケール: 1px = {args.scale}m, 1m = {args.sim_scale}単位")
    print(f"デフォルト幅: {args.default_width}m")
    print("=" * 60)

    try:
        # SVGからコース定義を生成
        course = svg_to_course_with_width(
            str(svg_path),
            args.scale,
            args.sim_scale,
            args.default_width
        )

        # JSONとして保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(course, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 60)
        print(f"✅ 変換完了: {output_path}")
        print(f"   壁の数: {len(course['walls'])}")
        for wall in course['walls']:
            print(f"   - {wall['name']}: {len(wall['vertices'])} 頂点")
        print("=" * 60)
        print("\n次のステップ:")
        print("1. JSONを編集してスタート/ゴール位置・角度を調整")
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
