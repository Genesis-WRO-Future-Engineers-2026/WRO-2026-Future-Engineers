"""コースのテスト"""

import pytest
import os
from src.physics.box2d_wrapper import PhysicsWorld
from src.env.course import Course


def get_test_course_path():
    """テスト用コースファイルのパスを取得"""
    return "courses/curriculum/level2_simple_oval.json"


def test_course_loading():
    """コースファイルが正しくロードできるか"""
    course_path = get_test_course_path()
    assert os.path.exists(course_path), f"Course file not found: {course_path}"

    course = Course(course_path)
    assert course is not None
    assert course.data is not None


def test_course_start_pose():
    """スタート位置と角度の取得"""
    course = Course(get_test_course_path())
    position, angle = course.get_start_pose()

    assert len(position) == 2
    assert isinstance(angle, (int, float))
    # simple_ovalの開始位置
    assert position == (1, 1)
    assert angle == 0.0


def test_course_goal_info():
    """ゴール情報の取得"""
    course = Course(get_test_course_path())
    position, radius = course.get_goal_info()

    assert len(position) == 2
    assert radius > 0
    assert position == (1, 1)


def test_course_walls_creation():
    """壁が正しく作成されるか"""
    world = PhysicsWorld()
    course = Course(get_test_course_path())

    course.create_walls(world.world)

    # 壁が作成されている
    assert len(course.walls) > 0
    # 外壁4辺 + 内壁4辺 = 8辺
    assert len(course.walls) == 8


def test_check_goal():
    """ゴール判定"""
    course = Course(get_test_course_path())

    # ゴール地点にいる
    assert course.check_goal((1, 1)) == True

    # ゴール近く（goal_radius=0.5m以内）
    assert course.check_goal((1.3, 1.2)) == True

    # ゴールから離れている
    assert course.check_goal((5.0, 5.0)) == False


def test_checkpoints():
    """チェックポイントの取得"""
    course = Course(get_test_course_path())
    checkpoints = course.get_checkpoints()

    assert len(checkpoints) > 0
    # simple_ovalは4つのチェックポイント
    assert len(checkpoints) == 4


def test_check_checkpoint():
    """チェックポイント通過判定"""
    course = Course(get_test_course_path())

    # 最初のチェックポイント付近
    assert course.check_checkpoint((5.0, 1.5), 0) == True

    # 離れている
    assert course.check_checkpoint((1.0, 1.0), 0) == False

    # 2番目のチェックポイント
    assert course.check_checkpoint((9.0, 5.0), 1) == True


def test_get_bounds():
    """コース境界の取得"""
    course = Course(get_test_course_path())
    min_x, max_x, min_y, max_y = course.get_bounds()

    assert min_x < max_x
    assert min_y < max_y

    # simple_ovalの境界
    assert min_x == 0
    assert max_x == 10
    assert min_y == 0
    assert max_y == 10
