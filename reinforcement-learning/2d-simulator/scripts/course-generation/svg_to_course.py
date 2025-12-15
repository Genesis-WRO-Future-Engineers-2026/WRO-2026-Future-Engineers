#!/usr/bin/env python3
"""
SVGファイルをコース定義JSONに変換

Figma/Inkscapeなどで作成したSVGパスを、
ミニカーシミュレーター用のJSON形式に変換する。

使用方法:
    python svg_to_course.py <svg_file> [options]

依存パッケージ:
    標準ライブラリのみ（追加インストール不要）
"""

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import List, Tuple


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
            # 最初の点に戻る（重複を避けるためスキップ）
            pass

        else:
            # その他のコマンド（S, Q, T, A など）は未実装
            pass

        i += 1

    return vertices


def svg_to_course(svg_file: str,
                  scale: float = 0.001,
                  sim_scale: float = 10.0) -> dict:
    """
    SVGファイルからコース定義JSONを生成

    Args:
        svg_file: SVGファイルのパス
        scale: px → m の変換係数（例: 0.001 = 1px = 1mm）
        sim_scale: m → シミュレーター単位（例: 10 = 1m = 10単位）

    Returns:
        コース定義辞書
    """
    print(f"📂 SVGファイルを読み込み中: {svg_file}")

    tree = ET.parse(svg_file)
    root = tree.getroot()

    # SVGの高さを取得（Y軸反転のため）
    svg_height = float(root.get('height', 0))
    print(f"  SVG高さ: {svg_height}px")

    # SVGの名前空間を取得
    # rootタグから名前空間を抽出（{namespace}tagname形式）
    ns = {}
    if '}' in root.tag:
        namespace = root.tag.split('}')[0].strip('{')
        ns = {'svg': namespace}

    # パス要素を検索（名前空間あり・なし両方に対応）
    if ns:
        paths = root.findall('.//svg:path', ns)
    else:
        paths = root.findall('.//path')

    if len(paths) == 0:
        print("警告: SVGファイル内にパスが見つかりません")

    walls = []
    for i, path_elem in enumerate(paths):
        d = path_elem.get('d')
        if not d:
            continue

        # 座標を抽出
        vertices_px = parse_svg_path_data(d)

        if len(vertices_px) < 3:
            print(f"  スキップ: パス#{i} (頂点数が少なすぎる)")
            continue

        # スケール変換（Y軸を反転）
        vertices = []
        for x, y in vertices_px:
            x_sim = x * scale * sim_scale
            # Y軸を反転: SVGは上が0、シミュレーターは下が0
            y_flipped = svg_height - y
            y_sim = y_flipped * scale * sim_scale
            vertices.append([round(x_sim, 2), round(y_sim, 2)])

        # 壁として追加
        name = path_elem.get('id', f'wall_{i}')
        walls.append({
            "type": "polygon",
            "name": name,
            "vertices": vertices
        })

        print(f"  ✓ {name}: {len(vertices)} 頂点")

    # コース定義を構築
    course = {
        "name": "Real Course - From SVG",
        "description": "Figma/InkscapeからエクスポートしたSVG",
        "difficulty": "medium",
        "start_position": [3.0, 10.0],  # TODO: 調整が必要
        "start_angle": 0.0,
        "goal_position": [3.0, 10.0],  # TODO: 調整が必要
        "goal_radius": 1.0,
        "walls": walls,
        "checkpoints": []  # TODO: 後で追加
    }

    return course


def main():
    parser = argparse.ArgumentParser(
        description="SVGファイルからコース定義JSONを生成"
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
    print("🎨 SVG → JSON 変換")
    print("=" * 60)
    print(f"入力: {svg_path}")
    print(f"出力: {output_path}")
    print(f"スケール: 1px = {args.scale}m, 1m = {args.sim_scale}単位")
    print("=" * 60)

    try:
        # SVGからコース定義を生成
        course = svg_to_course(str(svg_path), args.scale, args.sim_scale)

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
