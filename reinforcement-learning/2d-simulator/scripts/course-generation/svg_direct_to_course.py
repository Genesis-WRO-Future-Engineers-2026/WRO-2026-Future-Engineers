#!/usr/bin/env python3
"""
SVGから外壁・内壁を直接抽出してコース定義を生成

SVGに既に描画された外壁・内壁のパスを使用する
（中心線からの生成ではない）
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
    """SVGパスをMコマンドで分割"""
    segments = re.split(r'(?=[Mm])', d.strip())
    return [seg.strip() for seg in segments if seg.strip()]


def parse_svg_path_data(d: str) -> List[Tuple[float, float]]:
    """SVGパスデータから座標を抽出"""
    vertices = []
    tokens = re.findall(r'[MLHVCSQTAZmlhvcsqtaz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', d)

    current_x, current_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    i = 0

    while i < len(tokens):
        cmd = tokens[i]

        if cmd in ['M', 'm']:
            i += 1
            x = float(tokens[i])
            i += 1
            y = float(tokens[i])
            if cmd == 'm':
                x += current_x
                y += current_y
            current_x, current_y = x, y
            start_x, start_y = x, y
            vertices.append((x, y))

        elif cmd in ['L', 'l']:
            i += 1
            x = float(tokens[i])
            i += 1
            y = float(tokens[i])
            if cmd == 'l':
                x += current_x
                y += current_y
            current_x, current_y = x, y
            vertices.append((x, y))

        elif cmd in ['H', 'h']:
            i += 1
            x = float(tokens[i])
            if cmd == 'h':
                x += current_x
            current_x = x
            vertices.append((current_x, current_y))

        elif cmd in ['V', 'v']:
            i += 1
            y = float(tokens[i])
            if cmd == 'v':
                y += current_y
            current_y = y
            vertices.append((current_x, current_y))

        elif cmd in ['Z', 'z']:
            current_x, current_y = start_x, start_y
            if len(vertices) > 0 and vertices[-1] != (start_x, start_y):
                vertices.append((start_x, start_y))

        i += 1

    return vertices


def is_closed_loop(vertices: List[Tuple[float, float]]) -> bool:
    """パスが閉じたループかチェック"""
    if len(vertices) < 3:
        return False
    first = vertices[0]
    last = vertices[-1]
    return abs(first[0] - last[0]) < 1 and abs(first[1] - last[1]) < 1


def calculate_area(vertices: List[Tuple[float, float]]) -> float:
    """ポリゴンの面積を計算（Shoelace formula）"""
    if len(vertices) < 3:
        return 0.0

    area = 0.0
    for i in range(len(vertices)):
        j = (i + 1) % len(vertices)
        area += vertices[i][0] * vertices[j][1]
        area -= vertices[j][0] * vertices[i][1]
    return abs(area) / 2.0


def svg_to_course(svg_file: str,
                 scale: float = 0.001,
                 sim_scale: float = 10.0,
                 outer_index: int = None,
                 inner_index: int = None) -> dict:
    """
    SVGファイルから外壁・内壁を直接抽出してコース定義を生成

    Args:
        svg_file: SVGファイルのパス
        scale: px → m の変換係数
        sim_scale: m → シミュレーター単位
        outer_index: 外壁として使用するサブパスのインデックス（Noneの場合は自動選択）
        inner_index: 内壁として使用するサブパスのインデックス（Noneの場合は自動選択）

    Returns:
        コース定義辞書
    """
    print(f"📂 SVGファイルを読み込み中: {svg_file}")

    tree = ET.parse(svg_file)
    root = tree.getroot()

    # パス要素を検索
    paths = root.findall('.//{http://www.w3.org/2000/svg}path')
    if not paths:
        paths = root.findall('.//path')

    if len(paths) == 0:
        print("❌ エラー: SVGファイル内にパスが見つかりません")
        sys.exit(1)

    print(f"✓ {len(paths)}個のパス要素を検出")

    # すべてのサブパスを解析
    all_subpaths = []

    for i, path_elem in enumerate(paths):
        d = path_elem.get('d')
        if not d:
            continue

        subpaths = split_path_by_moveto(d)
        print(f"  パス#{i}: {len(subpaths)}個のサブパス")

        for j, subpath_d in enumerate(subpaths):
            vertices = parse_svg_path_data(subpath_d)
            if len(vertices) >= 3 and is_closed_loop(vertices):
                area = calculate_area(vertices)
                all_subpaths.append({
                    'index': (i, j),
                    'vertices': vertices,
                    'count': len(vertices),
                    'area': area
                })
                print(f"    サブパス#{j}: {len(vertices)} 頂点, 面積={area:.0f}")

    if len(all_subpaths) < 2:
        print("❌ エラー: 閉じたループが2つ以上必要です（外壁と内壁）")
        sys.exit(1)

    # 面積でソート（大きい順）
    all_subpaths.sort(key=lambda x: x['area'], reverse=True)

    # 外壁・内壁を選択
    if outer_index is not None:
        outer_wall = all_subpaths[outer_index]
    else:
        # 最も大きいループを外壁とする
        outer_wall = all_subpaths[0]

    if inner_index is not None:
        inner_wall = all_subpaths[inner_index]
    else:
        # 2番目に大きいループを内壁とする
        inner_wall = all_subpaths[1]

    print(f"\n✓ 選択:")
    print(f"  外壁: パス#{outer_wall['index'][0]}-サブパス#{outer_wall['index'][1]} "
          f"({outer_wall['count']} 頂点, 面積={outer_wall['area']:.0f})")
    print(f"  内壁: パス#{inner_wall['index'][0]}-サブパス#{inner_wall['index'][1]} "
          f"({inner_wall['count']} 頂点, 面積={inner_wall['area']:.0f})")

    # シミュレーター座標系に変換
    def convert_to_sim(vertices_px):
        vertices = []
        for x, y in vertices_px:
            x_sim = x * scale * sim_scale
            y_sim = y * scale * sim_scale
            vertices.append([round(x_sim, 2), round(y_sim, 2)])
        return vertices

    outer_wall_sim = convert_to_sim(outer_wall['vertices'])
    inner_wall_sim = convert_to_sim(inner_wall['vertices'])

    # 中心点を計算（スタート/ゴール位置の参考）
    outer_center_x = sum(v[0] for v in outer_wall_sim) / len(outer_wall_sim)
    outer_center_y = sum(v[1] for v in outer_wall_sim) / len(outer_wall_sim)

    # コース定義を構築
    course = {
        "name": "Real Course - From SVG (Direct)",
        "description": "SVGの外壁・内壁パスから直接生成",
        "difficulty": "hard",
        "start_position": [round(outer_center_x, 2), round(outer_center_y, 2)],
        "start_angle": 0.0,
        "goal_position": [round(outer_center_x, 2), round(outer_center_y, 2)],
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
        "checkpoints": []
    }

    return course


def main():
    parser = argparse.ArgumentParser(
        description="SVGから外壁・内壁を直接抽出してコース定義JSONを作成"
    )
    parser.add_argument("svg_file", help="入力SVGファイルのパス")
    parser.add_argument(
        "-o", "--output",
        help="出力JSONファイルのパス（デフォルト: courses/real/<svg名>_direct.json）"
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
        "--outer-index",
        type=int,
        help="外壁として使用するサブパスのインデックス（0から開始）"
    )
    parser.add_argument(
        "--inner-index",
        type=int,
        help="内壁として使用するサブパスのインデックス（0から開始）"
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
        output_path = Path("courses/real") / f"{svg_path.stem}_direct.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🎨 SVG → JSON 変換（直接抽出）")
    print("=" * 60)
    print(f"入力: {svg_path}")
    print(f"出力: {output_path}")
    print(f"スケール: 1px = {args.scale}m, 1m = {args.sim_scale}単位")
    print("=" * 60)

    try:
        # SVGからコース定義を生成
        course = svg_to_course(
            str(svg_path),
            args.scale,
            args.sim_scale,
            args.outer_index,
            args.inner_index
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
