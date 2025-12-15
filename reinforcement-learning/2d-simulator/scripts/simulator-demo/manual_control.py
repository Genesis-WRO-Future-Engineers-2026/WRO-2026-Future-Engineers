"""手動制御でシミュレーターをテスト"""

import sys
import os
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pygame
import numpy as np
from src.env.minicar_env import MinicarEnv


def get_available_courses(courses_dir: str = "courses") -> dict:
    """利用可能なコースファイルを取得

    Returns:
        dict: 難易度レベル別のコースファイル辞書
    """
    courses = {
        "easy": [],
        "medium": [],
        "hard": []
    }

    courses_path = Path(courses_dir)
    if not courses_path.exists():
        return courses

    for level in courses.keys():
        level_path = courses_path / level
        if level_path.exists():
            json_files = sorted(level_path.glob("*.json"))
            courses[level] = [str(f) for f in json_files]

    return courses


def print_available_courses(courses: dict):
    """利用可能なコースを表示"""
    print("利用可能なコース:")
    for level, course_list in courses.items():
        if course_list:
            print(f"\n  [{level.upper()}]")
            for i, course in enumerate(course_list, 1):
                course_name = Path(course).stem
                print(f"    {i}. {course_name} ({course})")


def main():
    """手動制御のメインループ"""
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description="ミニカー2Dシミュレーター - 手動制御モード")
    parser.add_argument(
        "--course",
        type=str,
        default="courses/curriculum/level2_simple_oval.json",
        help="コースファイルのパス (デフォルト: courses/curriculum/level2_simple_oval.json)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="利用可能なコース一覧を表示"
    )
    args = parser.parse_args()

    # 利用可能なコースを取得
    available_courses = get_available_courses()

    # コース一覧表示モード
    if args.list:
        print("=" * 60)
        print("ミニカー2Dシミュレーター - コース一覧")
        print("=" * 60)
        print()
        print_available_courses(available_courses)
        print()
        print("=" * 60)
        print("使用例:")
        print("  python scripts/simulator-demo/manual_control.py --course courses/curriculum/level3_narrow_oval.json")
        print("=" * 60)
        return

    # コースファイルの存在確認
    course_path = Path(args.course)
    if not course_path.exists():
        print(f"エラー: コースファイルが見つかりません: {args.course}")
        print()
        print_available_courses(available_courses)
        sys.exit(1)

    print("=" * 60)
    print("ミニカー2Dシミュレーター - 手動制御モード")
    print("=" * 60)
    print()
    print(f"コース: {args.course}")
    print()
    print("操作方法:")
    print("  ↑ / W     : 前進")
    print("  ↓ / S     : 後退")
    print("  ← / A     : 左旋回")
    print("  → / D     : 右旋回")
    print("  R         : リセット")
    print("  ESC / Q   : 終了")
    print()
    print("=" * 60)

    # 環境作成
    env = MinicarEnv(
        course_file=args.course, render_mode="human"
    )

    # リセット
    obs, info = env.reset()

    # メインループ
    running = True
    clock = pygame.time.Clock()
    step_count = 0

    while running:
        # デフォルトの行動（停止）
        steering = 0.0
        throttle = 0.0

        # キー入力
        keys = pygame.key.get_pressed()

        # ステアリング
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            steering = -1.0
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            steering = 1.0

        # スロットル
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            throttle = 1.0
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            throttle = -0.5  # 後退

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    # リセット
                    obs, info = env.reset()
                    step_count = 0
                    print("環境をリセットしました")

        # 行動を実行
        action = np.array([steering, throttle])
        obs, reward, terminated, truncated, info = env.step(action)
        step_count += 1

        # キー入力と車体状態のログ出力（10ステップごと）
        if step_count % 10 == 0:
            print(f"[Step {step_count:4d}] Steering: {steering:+.2f}, Throttle: {throttle:+.2f} | Speed: {info.get('speed', 0):.2f} m/s, Position: ({obs[0]:.2f}, {obs[1]:.2f}), Angle: {obs[2]:.2f} rad")

        # 描画
        env.render()

        # 終了判定
        if terminated or truncated:
            print()
            print("エピソード終了!")
            print(f"  ステップ数: {info['step_count']}")
            print(f"  総報酬: {info['total_reward']:.2f}")
            print(f"  チェックポイント通過: {info['next_checkpoint_index']}/{info['total_checkpoints']}")
            print(f"  最終速度: {info['speed']:.2f} m/s")
            print()

            if terminated and info["min_distance"] < 0.1:
                print("壁に衝突しました！")
            elif terminated:
                print("ゴール到達！おめでとうございます！")
            else:
                print("時間切れです")

            print("Rキーでリセット、ESCで終了")
            print()

            # 自動リセット（オプション）
            # obs, info = env.reset()

        # フレームレート制限
        clock.tick(30)  # 30 FPS

    # 終了処理
    env.close()
    print("シミュレーターを終了しました")


if __name__ == "__main__":
    main()
