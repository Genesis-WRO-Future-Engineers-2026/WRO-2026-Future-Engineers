#!/usr/bin/env python3
"""カスタムバリエーション生成スクリプト

異なるノイズレベルとスケールのバリエーションを生成
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from create_course_variations import load_course, save_course, create_variation
from pathlib import Path


def main():
    # ベースコース
    base_course_path = "courses/real/real-course_course.json"
    output_dir = Path("courses/real/variations")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("カスタムバリエーション生成")
    print("=" * 60)
    print(f"元コース: {base_course_path}")
    print(f"出力先: {output_dir}")
    print("=" * 60)

    # ベースコースをロード
    base_course = load_course(base_course_path)
    print(f"✅ Loaded base course: {base_course['name']}\n")

    # バリエーション設定
    variations = [
        {"id": 1, "noise": 0.03, "scale": 1.0, "desc": "小ノイズ(±3cm)"},
        {"id": 2, "noise": 0.05, "scale": 1.0, "desc": "中ノイズ(±5cm)"},
        {"id": 3, "noise": 0.08, "scale": 1.0, "desc": "大ノイズ(±8cm)"},
        {"id": 4, "noise": 0.0, "scale": 1.05, "desc": "壁幅1.05倍拡大"},
        {"id": 5, "noise": 0.0, "scale": 0.95, "desc": "壁幅0.95倍縮小"},
    ]

    # バリエーション生成
    for var_config in variations:
        print(f"生成中: Variation {var_config['id']} - {var_config['desc']}")

        variation = create_variation(
            base_course,
            variation_id=var_config["id"],
            noise_scale=var_config["noise"],
            scale_factor=var_config["scale"],
            seed=42 + var_config["id"]
        )

        # 保存
        output_file = output_dir / f"real_course_var{var_config['id']}.json"
        save_course(variation, str(output_file))

    print("\n" + "=" * 60)
    print("✅ 5個のカスタムバリエーション生成完了！")
    print("=" * 60)
    print("\nバリエーション一覧:")
    for var_config in variations:
        print(f"  var{var_config['id']}: {var_config['desc']}")
    print("\n" + "=" * 60)
    print("次のステップ:")
    print("1. 手動操作で確認:")
    print("   ./scripts/simulator-demo/run_manual_control.sh --course courses/real/variations/real_course_var1.json")
    print("\n2. 学習開始:")
    print("   python scripts/rl-training/train.py --course courses/real/variations/real_course_var1.json --gui")
    print("=" * 60)


if __name__ == "__main__":
    main()
