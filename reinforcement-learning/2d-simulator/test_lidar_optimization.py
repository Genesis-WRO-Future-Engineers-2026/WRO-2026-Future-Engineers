"""LiDAR最適化の簡易テスト"""

import numpy as np
import time
from src.env.minicar_env import MinicarEnv

def test_basic_functionality():
    """基本動作が正しいか確認"""
    print("=" * 60)
    print("テスト1: 基本動作の確認")
    print("=" * 60)

    env = MinicarEnv(render_mode=None)

    # リセット
    obs, info = env.reset()
    print(f"✅ reset()成功")
    print(f"   観測空間のサイズ: {obs.shape} (期待値: (77,))")
    assert obs.shape == (77,), f"観測サイズが不正: {obs.shape}"

    # ステップ実行
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)

    print(f"✅ step()成功")
    print(f"   観測: {obs.shape}")
    print(f"   報酬: {reward:.4f}")
    print(f"   終了: terminated={terminated}, truncated={truncated}")
    print(f"   情報: min_distance={info['min_distance']:.4f}")

    assert obs.shape == (77,), "観測が正しく返される"
    assert isinstance(reward, float), "報酬が返される"
    assert isinstance(terminated, bool), "終了フラグが返される"
    assert "min_distance" in info, "情報辞書が正しい"

    env.close()
    print("\n✅ 基本動作テスト: PASS\n")


def test_cache_consistency():
    """キャッシュされたデータが一貫していることを確認"""
    print("=" * 60)
    print("テスト2: キャッシュの整合性確認")
    print("=" * 60)

    env = MinicarEnv(render_mode=None)
    env.reset()

    # 1ステップ実行
    action = np.array([0.5, 0.8])
    obs, reward, terminated, truncated, info = env.step(action)

    # キャッシュの存在確認
    assert env._cached_lidar_scan is not None, "LiDARキャッシュが存在する"
    assert env._cached_vehicle_state is not None, "状態キャッシュが存在する"
    print("✅ キャッシュが存在する")

    # キャッシュとget_state()の一致確認
    current_state = env.vehicle.get_state()
    assert env._cached_vehicle_state["position"] == current_state["position"], "位置が一致"
    assert env._cached_vehicle_state["angle"] == current_state["angle"], "角度が一致"
    print("✅ キャッシュが現在の状態と一致")

    # キャッシュされたLiDARスキャンのサイズ確認
    assert env._cached_lidar_scan.shape == (72,), "LiDARスキャンのサイズが正しい"
    print(f"✅ LiDARスキャンのサイズが正しい: {env._cached_lidar_scan.shape}")

    env.close()
    print("\n✅ キャッシュ整合性テスト: PASS\n")


def test_performance():
    """パフォーマンスを測定"""
    print("=" * 60)
    print("テスト3: パフォーマンス測定")
    print("=" * 60)

    env = MinicarEnv(render_mode=None)
    env.reset()

    # 100ステップ実行して時間を測定
    num_steps = 100
    start_time = time.time()

    for _ in range(num_steps):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            env.reset()

    elapsed_time = time.time() - start_time
    fps = num_steps / elapsed_time
    avg_time_per_step = (elapsed_time / num_steps) * 1000  # ms

    print(f"✅ パフォーマンス測定結果:")
    print(f"   実行時間: {elapsed_time:.2f}秒")
    print(f"   FPS: {fps:.1f}")
    print(f"   1ステップあたり: {avg_time_per_step:.2f}ms")

    env.close()
    print("\n✅ パフォーマンステスト: PASS\n")


def test_multiple_episodes():
    """複数エピソードでの動作確認"""
    print("=" * 60)
    print("テスト4: 複数エピソードでの動作確認")
    print("=" * 60)

    env = MinicarEnv(render_mode=None)

    num_episodes = 3
    max_steps_per_episode = 50

    for episode in range(num_episodes):
        obs, info = env.reset()
        total_reward = 0

        for step in range(max_steps_per_episode):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward

            if terminated or truncated:
                break

        print(f"✅ エピソード {episode + 1}: {step + 1}ステップ, 総報酬={total_reward:.2f}")

    env.close()
    print("\n✅ 複数エピソードテスト: PASS\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LiDAR最適化 - 動作テスト")
    print("=" * 60 + "\n")

    try:
        test_basic_functionality()
        test_cache_consistency()
        test_performance()
        test_multiple_episodes()

        print("=" * 60)
        print("✅ すべてのテストが成功しました！")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ テスト失敗: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
