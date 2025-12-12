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
        # ノイズのみ（各頂点に個別ノイズ）
        {"id": 1, "noise": 0.01, "translation": 0.0, "desc": "極小ノイズ(±1cm)"},
        {"id": 2, "noise": 0.02, "translation": 0.0, "desc": "小ノイズ(±2cm)"},
        {"id": 3, "noise": 0.03, "translation": 0.0, "desc": "ノイズ(±3cm)"},
        {"id": 4, "noise": 0.05, "translation": 0.0, "desc": "中ノイズ(±5cm)"},
        {"id": 5, "noise": 0.07, "translation": 0.0, "desc": "大ノイズ(±7cm)"},
        {"id": 6, "noise": 0.10, "translation": 0.0, "desc": "特大ノイズ(±10cm)"},

        # 壁のずれ（隙間を作る）
        {"id": 7, "noise": 0.0, "translation": 0.02, "desc": "壁ずれ小(±2cm)"},
        {"id": 8, "noise": 0.0, "translation": 0.05, "desc": "壁ずれ中(±5cm)"},
        {"id": 9, "noise": 0.0, "translation": 0.08, "desc": "壁ずれ大(±8cm)"},

        # 組み合わせ
        {"id": 10, "noise": 0.02, "translation": 0.03, "desc": "ノイズ+壁ずれ(小)"},
        {"id": 11, "noise": 0.05, "translation": 0.05, "desc": "ノイズ+壁ずれ(中)"},
        {"id": 12, "noise": 0.07, "translation": 0.08, "desc": "ノイズ+壁ずれ(大)"},
    ]

    # バリエーション生成
    for var_config in variations:
        print(f"生成中: Variation {var_config['id']} - {var_config['desc']}")

        variation = create_variation(
            base_course,
            variation_id=var_config["id"],
            noise_scale=var_config["noise"],
            translation_scale=var_config["translation"],
            seed=42 + var_config["id"]
        )

        # 保存
        output_file = output_dir / f"real_course_var{var_config['id']}.json"
        save_course(variation, str(output_file))

    print("\n" + "=" * 60)
    print("✅ 12個のカスタムバリエーション生成完了！")
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
