#!/usr/bin/env python3
"""
設計図画像からコース輪郭を抽出するスクリプト

使用方法:
    python extract_from_image.py <image_file> [options]

依存パッケージ:
    pip install opencv-python numpy matplotlib
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import matplotlib.pyplot as plt

def load_and_preprocess_image(image_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    画像を読み込んで前処理

    Args:
        image_path: 画像ファイルのパス

    Returns:
        (元画像, グレースケール画像)
    """
    print(f"📂 画像を読み込み中: {image_path}")

    # 画像読み込み
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"画像が読み込めません: {image_path}")

    print(f"✓ 画像サイズ: {img.shape[1]} x {img.shape[0]}")

    # グレースケール変換
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    return img, gray


def extract_track_contours(gray: np.ndarray,
                          threshold: int = 127,
                          min_area: int = 1000,
                          show_preview: bool = False) -> List[np.ndarray]:
    """
    トラックの輪郭を抽出

    Args:
        gray: グレースケール画像
        threshold: 二値化の閾値
        min_area: 検出する最小面積
        show_preview: プレビューを表示するか

    Returns:
        輪郭のリスト
    """
    print("🔍 輪郭を抽出中...")

    # 二値化
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    # ノイズ除去
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # 輪郭検出
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    print(f"  検出された輪郭数: {len(contours)}")

    # 面積でフィルタリング
    valid_contours = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area > min_area:
            valid_contours.append((area, contour))
            print(f"  輪郭#{i}: 面積 {area:.0f}px²")

    # 面積でソート（大きい順）
    valid_contours.sort(key=lambda x: x[0], reverse=True)

    if show_preview:
        # プレビュー表示
        preview = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        for i, (area, contour) in enumerate(valid_contours[:5]):
            color = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 255, 0), (0, 255, 255)][i]
            cv2.drawContours(preview, [contour], -1, color, 2)

        plt.figure(figsize=(12, 8))
        plt.subplot(121)
        plt.imshow(binary, cmap='gray')
        plt.title('二値化画像')
        plt.axis('off')

        plt.subplot(122)
        plt.imshow(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB))
        plt.title('検出された輪郭（上位5つ）')
        plt.axis('off')

        plt.tight_layout()
        plt.show()

    return [c for _, c in valid_contours]


def simplify_and_convert_contour(contour: np.ndarray,
                                 epsilon_factor: float = 0.005) -> List[List[int]]:
    """
    輪郭を簡略化して座標リストに変換

    Args:
        contour: OpenCVの輪郭
        epsilon_factor: 簡略化の係数（小さいほど詳細）

    Returns:
        [[x, y], ...] 形式の座標リスト
    """
    # 輪郭の長さを計算
    perimeter = cv2.arcLength(contour, True)

    # 簡略化
    epsilon = epsilon_factor * perimeter
    approx = cv2.approxPolyDP(contour, epsilon, True)

    # 座標リストに変換
    vertices = []
    for point in approx:
        x, y = point[0]
        vertices.append([int(x), int(y)])

    print(f"  簡略化: {len(contour)} → {len(vertices)} 頂点")

    return vertices


def scale_to_simulator(vertices: List[List[int]],
                      img_width: int,
                      img_height: int,
                      real_width_m: float = 3.0,
                      sim_scale: float = 10.0) -> List[List[float]]:
    """
    画像座標をシミュレーター座標に変換

    Args:
        vertices: 画像上の頂点リスト
        img_width: 画像の幅（ピクセル）
        img_height: 画像の高さ（ピクセル）
        real_width_m: 実物の幅（メートル）
        sim_scale: 1m = sim_scale単位

    Returns:
        シミュレーター座標の頂点リスト
    """
    print(f"📏 スケール変換中: 実寸 {real_width_m}m → シミュレーター座標")

    vertices_array = np.array(vertices, dtype=float)

    # ピクセルからメートルへの変換係数
    px_to_m = real_width_m / img_width

    # Y軸を反転（画像は上が0、シミュレーターは下が0）
    vertices_array[:, 1] = img_height - vertices_array[:, 1]

    # 原点を左下に
    min_x = vertices_array[:, 0].min()
    min_y = vertices_array[:, 1].min()
    vertices_array[:, 0] -= min_x
    vertices_array[:, 1] -= min_y

    # スケール変換
    vertices_scaled = vertices_array * px_to_m * sim_scale

    print(f"  変換後のサイズ: {vertices_scaled[:, 0].max():.2f} x {vertices_scaled[:, 1].max():.2f} 単位")

    # リストに変換（小数点2桁）
    result = [[round(x, 2), round(y, 2)] for x, y in vertices_scaled]

    return result


def interactive_contour_selection(img: np.ndarray,
                                  contours: List[np.ndarray]) -> Tuple[int, int]:
    """
    対話的に外周と内周を選択

    Args:
        img: 元画像
        contours: 輪郭のリスト

    Returns:
        (外周のインデックス, 内周のインデックス)
    """
    print("\n🖱️  輪郭を選択してください:")

    # プレビュー表示
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i in range(min(6, len(contours))):
        preview = img.copy()
        cv2.drawContours(preview, [contours[i]], -1, (0, 255, 0), 3)

        axes[i].imshow(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB))
        axes[i].set_title(f"輪郭 #{i}")
        axes[i].axis('off')

    plt.tight_layout()
    plt.show()

    # ユーザー入力
    outer_idx = int(input("外周の番号を入力: "))
    inner_idx = int(input("内周の番号を入力（なければ-1）: "))

    return outer_idx, inner_idx


def generate_course_json(outer_vertices: List[List[float]],
                        inner_vertices: List[List[List[float]]],
                        name: str = "Real Course - From Image") -> dict:
    """
    コース定義JSONを生成

    Args:
        outer_vertices: 外周の頂点
        inner_vertices: 内周の頂点リスト
        name: コース名

    Returns:
        コース定義辞書
    """
    print("📄 JSON定義を生成中...")

    # スタート/ゴール位置を左下付近に設定
    outer_array = np.array(outer_vertices)
    start_x = outer_array[:, 0].min() + 3.0
    start_y = (outer_array[:, 1].min() + outer_array[:, 1].max()) / 2

    course = {
        "name": name,
        "description": "設計図画像から抽出したコース",
        "difficulty": "medium",
        "start_position": [round(start_x, 2), round(start_y, 2)],
        "start_angle": 0.0,
        "goal_position": [round(start_x, 2), round(start_y, 2)],
        "goal_radius": 1.0,
        "walls": [
            {
                "type": "polygon",
                "name": "outer_wall",
                "vertices": outer_vertices
            }
        ],
        "checkpoints": []
    }

    # 内周を追加
    for i, inner in enumerate(inner_vertices):
        course["walls"].append({
            "type": "polygon",
            "name": f"inner_wall_{i}",
            "vertices": inner
        })

    print(f"✓ 壁の数: {len(course['walls'])}")

    return course


def main():
    parser = argparse.ArgumentParser(
        description="設計図画像からコース定義JSONを生成"
    )
    parser.add_argument("image_file", help="入力画像ファイルのパス")
    parser.add_argument("-o", "--output", help="出力JSONファイルのパス")
    parser.add_argument("-w", "--width", type=float, default=3.0,
                       help="実物のコース幅（メートル、デフォルト: 3.0）")
    parser.add_argument("-s", "--scale", type=float, default=10.0,
                       help="シミュレーター座標のスケール（1m=N単位、デフォルト: 10.0）")
    parser.add_argument("-t", "--threshold", type=int, default=127,
                       help="二値化の閾値（0-255、デフォルト: 127）")
    parser.add_argument("--min-area", type=int, default=5000,
                       help="検出する最小面積（ピクセル²、デフォルト: 5000）")
    parser.add_argument("--simplify", type=float, default=0.005,
                       help="輪郭簡略化の係数（デフォルト: 0.005）")
    parser.add_argument("--preview", action="store_true",
                       help="処理結果のプレビューを表示")
    parser.add_argument("--interactive", action="store_true",
                       help="対話的に輪郭を選択")

    args = parser.parse_args()

    # 入力ファイルの確認
    img_path = Path(args.image_file)
    if not img_path.exists():
        print(f"エラー: ファイルが見つかりません: {img_path}")
        sys.exit(1)

    # 出力ファイル名の決定
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path("courses/real") / f"{img_path.stem}_course.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🚗 設計図からコース生成")
    print("=" * 60)
    print(f"入力: {img_path}")
    print(f"出力: {output_path}")
    print("=" * 60)

    try:
        # Step 1: 画像読み込み
        img, gray = load_and_preprocess_image(str(img_path))

        # Step 2: 輪郭抽出
        contours = extract_track_contours(
            gray,
            threshold=args.threshold,
            min_area=args.min_area,
            show_preview=args.preview
        )

        if len(contours) == 0:
            print("エラー: 輪郭が検出できませんでした。")
            print("--threshold や --min-area を調整してください。")
            sys.exit(1)

        # Step 3: 輪郭選択
        if args.interactive:
            outer_idx, inner_idx = interactive_contour_selection(img, contours)
        else:
            # 自動選択（最大が外周、2番目が内周）
            outer_idx = 0
            inner_idx = 1 if len(contours) > 1 else -1
            print(f"  自動選択: 外周=#{outer_idx}, 内周=#{inner_idx}")

        # Step 4: 輪郭の簡略化
        outer_vertices_px = simplify_and_convert_contour(contours[outer_idx], args.simplify)

        inner_vertices_px = []
        if inner_idx >= 0 and inner_idx < len(contours):
            inner_vertices_px.append(
                simplify_and_convert_contour(contours[inner_idx], args.simplify)
            )

        # Step 5: スケール変換
        img_height, img_width = gray.shape

        outer_vertices = scale_to_simulator(
            outer_vertices_px, img_width, img_height, args.width, args.scale
        )

        inner_vertices = []
        for inner_px in inner_vertices_px:
            inner_sim = scale_to_simulator(
                inner_px, img_width, img_height, args.width, args.scale
            )
            inner_vertices.append(inner_sim)

        # Step 6: JSON生成
        course = generate_course_json(
            outer_vertices,
            inner_vertices,
            name=f"Real Course - {img_path.stem}"
        )

        # Step 7: 保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(course, f, indent=2, ensure_ascii=False)

        print("=" * 60)
        print(f"✅ コース定義を生成しました: {output_path}")
        print("=" * 60)
        print("\n次のステップ:")
        print("1. GUIで可視化して確認:")
        print(f"   python scripts/rl-training/train.py --course {output_path} --gui")
        print("2. JSONを編集してチェックポイントを追加")
        print("3. スタート/ゴール位置を調整")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
