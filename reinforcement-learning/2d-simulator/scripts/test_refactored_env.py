"""リファクタリング後の環境の動作確認テスト"""

import sys
import os

# PYTHONPATHの設定
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.env.minicar_env import MinicarEnv


def test_basic_functionality():
    """基本的な機能のテスト"""
    print("=" * 60)
    print("リファクタリング後の環境の動作確認テスト")
    print("=" * 60)

    # 環境の作成
    print("\n[TEST 1] 環境の作成...")
    try:
        env = MinicarEnv(
            course_file="courses/easy/simple_oval.json",
            max_steps=100,
        )
        print("✅ 環境の作成に成功")
    except Exception as e:
        print(f"❌ 環境の作成に失敗: {e}")
        return False

    # リセット
    print("\n[TEST 2] 環境のリセット...")
    try:
        obs, info = env.reset()
        assert obs.shape == (10,), f"観測空間の形状が間違っています: {obs.shape}"
        assert "position" in info, "infoにpositionが含まれていません"
        assert "total_reward" in info, "infoにtotal_rewardが含まれていません"
        print(f"✅ リセット成功: obs.shape={obs.shape}")
    except Exception as e:
        print(f"❌ リセットに失敗: {e}")
        return False

    # ステップ実行
    print("\n[TEST 3] ステップ実行...")
    try:
        action = np.array([0.0, 0.5])  # 直進
        obs, reward, terminated, truncated, info = env.step(action)

        assert obs.shape == (10,), f"観測空間の形状が間違っています: {obs.shape}"
        assert isinstance(reward, float), f"報酬がfloat型ではありません: {type(reward)}"
        assert isinstance(terminated, bool), f"terminatedがbool型ではありません: {type(terminated)}"
        assert isinstance(truncated, bool), f"truncatedがbool型ではありません: {type(truncated)}"

        print(f"✅ ステップ実行成功")
        print(f"   - obs.shape: {obs.shape}")
        print(f"   - reward: {reward:.4f}")
        print(f"   - terminated: {terminated}")
        print(f"   - truncated: {truncated}")
    except Exception as e:
        print(f"❌ ステップ実行に失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 複数ステップの実行
    print("\n[TEST 4] 複数ステップの実行（10ステップ）...")
    try:
        total_reward = 0.0
        for i in range(10):
            action = np.array([0.0, 0.5])
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward

            if terminated or truncated:
                print(f"   エピソード終了（ステップ{i+1}）")
                break

        print(f"✅ 複数ステップ実行成功")
        print(f"   - 総報酬: {total_reward:.4f}")
        print(f"   - 最終位置: {info['position']}")
        print(f"   - 最終速度: {info['speed']:.2f}")
    except Exception as e:
        print(f"❌ 複数ステップ実行に失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

    # クリーンアップ
    print("\n[TEST 5] 環境のクローズ...")
    try:
        env.close()
        print("✅ 環境のクローズ成功")
    except Exception as e:
        print(f"❌ 環境のクローズに失敗: {e}")
        return False

    print("\n" + "=" * 60)
    print("すべてのテストに成功しました！")
    print("=" * 60)
    return True


def test_backward_compatibility():
    """後方互換性のテスト"""
    print("\n" + "=" * 60)
    print("後方互換性のテスト")
    print("=" * 60)

    print("\n[TEST] 既存の使用方法が動作するか...")
    try:
        # 既存の使用方法
        env = MinicarEnv(
            course_file="courses/easy/simple_oval.json",
            render_mode=None,
            max_steps=100,
            deployment_mode=False,
            enable_domain_randomization=False,
            adaptive_reward_scaler=None,
        )

        obs, info = env.reset()
        action = np.array([0.0, 0.5])
        obs, reward, terminated, truncated, info = env.step(action)
        env.close()

        print("✅ 後方互換性テスト成功")
        return True
    except Exception as e:
        print(f"❌ 後方互換性テストに失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custom_reward():
    """カスタム報酬関数のテスト"""
    print("\n" + "=" * 60)
    print("カスタム報酬関数のテスト")
    print("=" * 60)

    print("\n[TEST] シンプルな報酬関数を使用...")
    try:
        from src.env.reward.factory import RewardFactory

        # シンプルな報酬関数を作成
        reward_fn = RewardFactory.create_simple_reward()

        # 環境を作成
        env = MinicarEnv(
            course_file="courses/easy/simple_oval.json",
            max_steps=100,
            reward_function=reward_fn,
        )

        obs, info = env.reset()
        action = np.array([0.0, 0.5])
        obs, reward, terminated, truncated, info = env.step(action)
        env.close()

        print("✅ カスタム報酬関数テスト成功")
        return True
    except Exception as e:
        print(f"❌ カスタム報酬関数テストに失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = True

    # 基本機能のテスト
    if not test_basic_functionality():
        success = False

    # 後方互換性のテスト
    if not test_backward_compatibility():
        success = False

    # カスタム報酬関数のテスト
    if not test_custom_reward():
        success = False

    # 結果
    print("\n" + "=" * 60)
    if success:
        print("🎉 すべてのテストに合格しました！")
    else:
        print("⚠️  一部のテストに失敗しました")
    print("=" * 60)

    sys.exit(0 if success else 1)
