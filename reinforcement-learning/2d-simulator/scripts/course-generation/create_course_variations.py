"""本番コースのバリエーション生成スクリプト

壁位置を少しずつランダムにずらして、複数のバリエーションを生成。
実機環境での壁位置のズレに対応するため（Domain Randomization）。
"""

import json
import random
import argparse
from pathlib import Path
import numpy as np


def load_course(course_file: str) -> dict:
    """コースJSONをロード"""
    with open(course_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_course(course_data: dict, output_file: str):
    """コースJSONを保存"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(course_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved: {output_file}")


def add_noise_to_vertices(vertices: list, noise_scale: float, seed: int = None) -> list:
    """頂点座標にノイズを追加

    Args:
        vertices: 頂点座標のリスト [[x1, y1], [x2, y2], ...]
        noise_scale: ノイズの大きさ（標準偏差、単位: メートル）
        seed: 乱数シード（再現性のため）

    Returns:
        ノイズを加えた頂点座標のリスト
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    noisy_vertices = []
    for vertex in vertices:
        x, y = vertex
        # ガウシアンノイズを追加
        noise_x = np.random.normal(0, noise_scale)
        noise_y = np.random.normal(0, noise_scale)
        noisy_vertices.append([x + noise_x, y + noise_y])

    return noisy_vertices


def scale_vertices(vertices: list, scale_factor: float, center: list = None) -> list:
    """頂点座標をスケール変換

    Args:
        vertices: 頂点座標のリスト [[x1, y1], [x2, y2], ...]
        scale_factor: スケール係数（1.0より大きいと拡大、小さいと縮小）
        center: スケールの中心点 [cx, cy]（Noneの場合は重心を使用）

    Returns:
        スケール変換後の頂点座標のリスト
    """
    if center is None:
        # 重心を計算
        cx = sum(v[0] for v in vertices) / len(vertices)
        cy = sum(v[1] for v in vertices) / len(vertices)
        center = [cx, cy]

    scaled_vertices = []
    for vertex in vertices:
        x, y = vertex
        # 中心からの相対座標をスケール
        dx = (x - center[0]) * scale_factor
        dy = (y - center[1]) * scale_factor
        scaled_vertices.append([center[0] + dx, center[1] + dy])

    return scaled_vertices


def create_variation(
    base_course: dict,
    variation_id: int,
    noise_scale: float = 0.0,
    scale_factor: float = 1.0,
    seed: int = None
) -> dict:
    """コースのバリエーションを生成

    Args:
        base_course: 元のコースデータ
        variation_id: バリエーションID
        noise_scale: 壁位置のノイズスケール（m）
        scale_factor: スケール係数（壁の拡大/縮小）
        seed: 乱数シード

    Returns:
        バリエーションコースデータ
    """
    # ディープコピー
    variation = json.loads(json.dumps(base_course))

    # 名前を変更
    desc_parts = []
    if noise_scale > 0:
        desc_parts.append(f"ノイズ±{noise_scale}m")
    if scale_factor != 1.0:
        desc_parts.append(f"スケール{scale_factor}x")
    description = ", ".join(desc_parts) if desc_parts else "オリジナル"

    variation["name"] = f"{base_course['name']} - Variation {variation_id}"
    variation["description"] = f"{description} (seed={seed})"

    # 各壁を変換
    for wall in variation["walls"]:
        if "vertices" in wall:
            vertices = wall["vertices"]

            # スケール変換
            if scale_factor != 1.0:
                vertices = scale_vertices(vertices, scale_factor)

            # ノイズ追加
            if noise_scale > 0:
                vertices = add_noise_to_vertices(
                    vertices,
                    noise_scale=noise_scale,
                    seed=seed
                )

            wall["vertices"] = vertices

    return variation


def main():
    parser = argparse.ArgumentParser(
        description="本番コースのバリエーションを生成"
    )
    parser.add_argument(
        "--base-course",
        type=str,
        default="courses/real/real_course_fixed.json",
        help="元となるコースファイル",
    )
    parser.add_argument(
        "--num-variations",
        type=int,
        default=5,
        help="生成するバリエーション数",
    )
    parser.add_argument(
        "--noise-scale",
        type=float,
        default=0.05,
        help="壁位置のノイズスケール（m）デフォルト: 0.05m = 5cm",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="courses/real/variations",
        help="出力ディレクトリ",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="ランダムシード（再現性のため）",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("本番コースバリエーション生成")
    print("=" * 60)
    print(f"元コース: {args.base_course}")
    print(f"バリエーション数: {args.num_variations}")
    print(f"壁位置ノイズ: ±{args.noise_scale}m")
    print(f"出力先: {args.output_dir}")
    print("=" * 60)

    # 元コースをロード
    base_course = load_course(args.base_course)
    print(f"✅ Loaded base course: {base_course['name']}")

    # 出力ディレクトリ作成
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # バリエーション生成
    for i in range(args.num_variations):
        # シード設定（再現性のため）
        seed = args.seed + i if args.seed is not None else None

        # バリエーション生成
        variation = create_variation(
            base_course,
            variation_id=i + 1,
            noise_scale=args.noise_scale,
            seed=seed
        )

        # 保存
        output_file = output_dir / f"real_course_var{i+1}.json"
        save_course(variation, str(output_file))

    print("\n" + "=" * 60)
    print(f"✅ {args.num_variations}個のバリエーション生成完了！")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. カリキュラム学習設定にバリエーションを追加")
    print("2. 学習開始:")
    print("   python scripts/rl-training/train_curriculum.py --total-iterations 200")
    print("=" * 60)


if __name__ == "__main__":
    main()
