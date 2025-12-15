#!/usr/bin/env python3
"""
SVGパスのデバッグ用スクリプト

各サブパスの座標を詳細に表示する
"""

import re
from pathlib import Path
from xml.etree import ElementTree as ET


def split_path_by_moveto(d: str):
    """SVGパスをMコマンドで分割"""
    segments = re.split(r'(?=[Mm])', d.strip())
    return [seg.strip() for seg in segments if seg.strip()]


def parse_svg_path_simple(d: str):
    """簡易的なSVGパスパーサー"""
    tokens = re.findall(r'[MLHVCSQTAZmlhvcsqtaz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', d)

    vertices = []
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
            if vertices[-1] != (start_x, start_y):
                vertices.append((start_x, start_y))

        i += 1

    return vertices


def main():
    svg_file = "doc/plan/real-course/real-course.svg"

    print(f"📂 SVGファイルを解析: {svg_file}\n")

    tree = ET.parse(svg_file)
    root = tree.getroot()

    # パスを検索
    paths = root.findall('.//{http://www.w3.org/2000/svg}path')
    if not paths:
        paths = root.findall('.//path')

    print(f"✓ {len(paths)}個のパス要素を検出\n")
    print("=" * 80)

    for path_idx, path_elem in enumerate(paths):
        d = path_elem.get('d')
        if not d:
            continue

        # サブパスに分割
        subpaths = split_path_by_moveto(d)

        print(f"\n📍 パス#{path_idx}: {len(subpaths)}個のサブパス")
        print("-" * 80)

        for sub_idx, subpath_d in enumerate(subpaths):
            vertices = parse_svg_path_simple(subpath_d)

            if len(vertices) < 2:
                continue

            print(f"\n  サブパス#{sub_idx}: {len(vertices)} 頂点")
            print(f"  生データ: {subpath_d[:100]}...")

            # 最初と最後の頂点を表示
            print(f"  始点: ({vertices[0][0]:.1f}, {vertices[0][1]:.1f})")
            print(f"  終点: ({vertices[-1][0]:.1f}, {vertices[-1][1]:.1f})")

            # 閉じているか確認
            is_closed = abs(vertices[0][0] - vertices[-1][0]) < 1 and \
                       abs(vertices[0][1] - vertices[-1][1]) < 1
            print(f"  閉じたループ: {'はい' if is_closed else 'いいえ'}")

            # すべての頂点を表示（長すぎる場合は省略）
            if len(vertices) <= 10:
                print(f"  全頂点:")
                for i, (x, y) in enumerate(vertices):
                    print(f"    {i}: ({x:.1f}, {y:.1f})")
            else:
                print(f"  最初の5頂点:")
                for i in range(min(5, len(vertices))):
                    x, y = vertices[i]
                    print(f"    {i}: ({x:.1f}, {y:.1f})")
                print(f"  ... ({len(vertices) - 10}個省略)")
                print(f"  最後の5頂点:")
                for i in range(max(5, len(vertices) - 5), len(vertices)):
                    x, y = vertices[i]
                    print(f"    {i}: ({x:.1f}, {y:.1f})")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
