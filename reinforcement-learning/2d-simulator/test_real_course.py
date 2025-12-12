"""本番コースの動作確認テスト"""

from src.env.minicar_env import MinicarEnv
import numpy as np

# 本番コースで環境作成
env = MinicarEnv(course_file="courses/real/real_course_fixed.json")

print("=" * 60)
print("本番コース動作確認")
print("=" * 60)

# リセット
obs, info = env.reset()
print(f"✅ リセット成功")
print(f"  観測空間: {obs.shape}")
print(f"  スタート位置: {info['position']}")
print(f"  チェックポイント総数: {info['total_checkpoints']}")

# 数ステップ実行
print(f"\n10ステップ実行中...")
for i in range(10):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)

    if terminated or truncated:
        print(f"  ステップ{i+1}で終了")
        break

print(f"✅ ステップ実行成功")
print(f"  最終報酬: {reward:.2f}")
print(f"  最終位置: {info['position']}")

env.close()

print("\n" + "=" * 60)
print("本番コース正常動作確認完了！")
print("=" * 60)
