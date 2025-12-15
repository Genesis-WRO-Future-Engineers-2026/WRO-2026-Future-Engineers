"""カリキュラム学習の基本動作テスト"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.curriculum.curriculum_manager import CurriculumManager
from src.env.minicar_env import MinicarEnv


def test_curriculum_manager():
    """CurriculumManagerの基本動作テスト"""
    print("=" * 60)
    print("Testing CurriculumManager")
    print("=" * 60)

    # コースリスト
    courses = [
        "courses/curriculum/level2_simple_oval.json",
        "courses/curriculum/level3_narrow_oval.json",
        "courses/curriculum/level4_s_curve.json",
    ]

    # CurriculumManagerの作成
    curriculum = CurriculumManager(
        courses=courses,
        success_threshold=0.8,
        degradation_threshold=0.3,
        evaluation_window=100,
        min_episodes_before_advance=50,
    )

    print(f"\nInitial state: {curriculum}")
    print(f"Current course: {curriculum.get_current_course()}")

    # レベル0: 成功を記録してレベルアップ
    print("\n" + "-" * 60)
    print("Level 0: Simulating high success rate (80%)")
    print("-" * 60)
    for i in range(60):
        success = i < 48  # 80% success rate
        curriculum.update(success)

    print(f"Success rate: {curriculum.get_success_rate():.2%}")
    print(f"Should advance? {curriculum.should_advance()}")

    result = curriculum.auto_adjust_level()
    print(f"Auto adjust result: {result}")
    print(f"Current state: {curriculum}")

    # レベル1: 中程度の成功率
    print("\n" + "-" * 60)
    print("Level 1: Simulating medium success rate (50%)")
    print("-" * 60)
    for i in range(60):
        success = i < 30  # 50% success rate
        curriculum.update(success)

    print(f"Success rate: {curriculum.get_success_rate():.2%}")
    print(f"Should advance? {curriculum.should_advance()}")
    print(f"Should degrade? {curriculum.should_degrade()}")

    result = curriculum.auto_adjust_level()
    print(f"Auto adjust result: {result}")
    print(f"Current state: {curriculum}")

    # 最終統計
    print("\n" + "=" * 60)
    print("Final Statistics")
    print("=" * 60)
    stats = curriculum.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    print("\n✓ CurriculumManager test completed!\n")


def test_course_loading():
    """コース動的ロードのテスト"""
    print("=" * 60)
    print("Testing Dynamic Course Loading")
    print("=" * 60)

    # 環境を作成
    env = MinicarEnv(
        course_file="courses/curriculum/level2_simple_oval.json",
        render_mode=None,
        max_steps=2000,
    )

    print(f"\nInitial course: {env.course.course_file}")
    print(f"Initial course data: {env.course.data.get('name', 'N/A')}")

    # コースを変更
    print("\n" + "-" * 60)
    print("Loading medium course...")
    print("-" * 60)
    env.load_course("courses/curriculum/level3_narrow_oval.json")
    print(f"New course: {env.course.course_file}")
    print(f"New course data: {env.course.data.get('name', 'N/A')}")

    # さらに変更
    print("\n" + "-" * 60)
    print("Loading hard course...")
    print("-" * 60)
    env.load_course("courses/curriculum/level4_s_curve.json")
    print(f"New course: {env.course.course_file}")
    print(f"New course data: {env.course.data.get('name', 'N/A')}")

    # 環境をクローズ
    env.close()

    print("\n✓ Course loading test completed!\n")


def test_curriculum_with_env():
    """CurriculumManagerと環境の統合テスト"""
    print("=" * 60)
    print("Testing Curriculum Integration with Environment")
    print("=" * 60)

    # コースリスト
    courses = [
        "courses/curriculum/level2_simple_oval.json",
        "courses/curriculum/level3_narrow_oval.json",
        "courses/curriculum/level4_s_curve.json",
    ]

    # CurriculumManagerの作成
    curriculum = CurriculumManager(
        courses=courses,
        success_threshold=0.8,
        degradation_threshold=0.3,
        evaluation_window=100,
        min_episodes_before_advance=50,
    )

    # 環境の作成
    env = MinicarEnv(
        course_file=curriculum.get_current_course(),
        render_mode=None,
        max_steps=2000,
    )

    print(f"\nInitial course: {env.course.data.get('name', 'N/A')}")
    print(f"Curriculum level: {curriculum.current_level}")

    # シミュレーション: 成功を記録してレベルアップ
    print("\n" + "-" * 60)
    print("Simulating successful episodes...")
    print("-" * 60)

    for i in range(60):
        # 成功を記録（80%の成功率）
        success = i < 48
        curriculum.update(success)

    # レベル調整
    result = curriculum.auto_adjust_level()
    if result == "advanced":
        print(f"✓ Level advanced to {curriculum.current_level}")
        # コースを変更
        new_course = curriculum.get_current_course()
        env.load_course(new_course)
        print(f"✓ Course changed to: {env.course.data.get('name', 'N/A')}")
    else:
        print(f"Level not changed: {result}")

    # 環境をクローズ
    env.close()

    print("\n✓ Integration test completed!\n")


def main():
    """全テストを実行"""
    print("\n" + "=" * 60)
    print("CURRICULUM LEARNING BASIC TESTS")
    print("=" * 60 + "\n")

    try:
        # Test 1: CurriculumManager
        test_curriculum_manager()

        # Test 2: Dynamic course loading
        test_course_loading()

        # Test 3: Integration with environment
        test_curriculum_with_env()

        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print("TEST FAILED! ✗")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
