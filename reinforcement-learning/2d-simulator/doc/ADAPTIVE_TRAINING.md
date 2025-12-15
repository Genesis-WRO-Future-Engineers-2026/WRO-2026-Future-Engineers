# 適応的学習システム

学習の安定性を最優先した新しい学習システムです。

## 概要

### 3つの主要機能

1. **段階的カリキュラム学習** - 超簡単なコースから徐々に難易度を上げる
2. **適応的報酬スケーリング** - 学習の進捗に応じて報酬係数を自動調整
3. **学習監視** - 成功率とフェーズ遷移を自動追跡

### 従来の問題点と解決策

| 問題 | 従来 | 新システム |
|------|------|------------|
| 学習不安定 | いきなり難しいコース | 6段階のカリキュラム |
| 報酬係数の調整 | 手動で試行錯誤（v3.0→v3.1→v3.2） | 自動的にフェーズ遷移 |
| 進捗が不明 | Success Rate 0%が続く | レベルごとに評価 |

---

## カリキュラム学習

### レベル構成

**すべてのコースは `courses/curriculum/` ディレクトリに統一されています**

```
Level 0: 直線コース (curriculum/level0_straight.json)
  - 目的: 壁回避の基礎
  - チェックポイント: なし
  - 難易度: ★☆☆☆☆☆（超簡単）

Level 1: 単純カーブ (curriculum/level1_simple_curve.json)
  - 目的: 操舵の基礎
  - チェックポイント: 1個
  - 難易度: ★★☆☆☆☆（簡単）

Level 2: 標準楕円 (curriculum/level2_simple_oval.json)
  - 目的: 周回走行の基礎
  - チェックポイント: 4個
  - 難易度: ★★★☆☆☆（easy）

Level 3: 狭い楕円 (curriculum/level3_narrow_oval.json)
  - 目的: より正確な操舵
  - チェックポイント: 4個
  - 難易度: ★★★★☆☆（medium）

Level 4: S字カーブ (curriculum/level4_s_curve.json)
  - 目的: 複雑な経路
  - チェックポイント: 4個
  - 難易度: ★★★★★☆（hard）

Level 5: 実コース (curriculum/level5_real_course.json)
  - 目的: 実機転移
  - チェックポイント: 5個
  - 難易度: ★★★★★★（最終目標）
```

### レベルアップ条件

- **Success Rate ≥ 80%** を達成
- **最低50エピソード** 完了
- 自動的に次のレベルへ遷移

### レベルダウン条件

- **Success Rate < 30%** が続く場合
- 前のレベルに戻って再学習

---

## 適応的報酬スケーリング

### 3つのフェーズ

#### Phase 0: 基礎走行（初期）
```python
time_penalty = 0.3           # 弱め - まず動けるようにする
direction_reward = 1.2       # 強め - チェックポイントへ誘導
checkpoint_reward = 150.0
```

**目的**: 壁にぶつからずに走行できるようになる

**期待される行動**:
- ランダムな動き → 壁回避
- チェックポイントを発見
- 基本的な操舵

#### Phase 1: 探索（中期）
```python
time_penalty = 0.5           # 中程度
direction_reward = 0.8       # やや弱め
checkpoint_reward = 200.0    # 強め - 通過を重視
```

**目的**: チェックポイントを通過できるようになる

**期待される行動**:
- チェックポイントへ接近
- チェックポイント通過
- ゴールを目指す

#### Phase 2: 最適化（後期）
```python
time_penalty = 0.7           # 強め - 速度最適化
direction_reward = 0.5       # 弱め - もう学習済み
time_bonus_scale = 2.5       # 強め - 早いほど高報酬
```

**目的**: なるべく早くゴールに到達する

**期待される行動**:
- 最短ルート選択
- 速度最適化
- 安定したゴール到達

### フェーズ遷移条件

| 遷移 | 条件 |
|------|------|
| Phase 0 → 1 | Success Rate ≥ 30%, Avg CP Passed ≥ 50%, 100エピソード以上 |
| Phase 1 → 2 | Success Rate ≥ 60%, Avg CP Passed ≥ 80%, 100エピソード以上 |

---

## 使い方

### 基本的な学習

```bash
# 環境をアクティベート
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# 適応的学習を開始（GUI付き）
python scripts/rl-training/train_adaptive.py --gui --total-iterations 500

# GUIなし高速学習
python scripts/rl-training/train_adaptive.py --total-iterations 2000
```

### 学習の進捗確認

```bash
# TensorBoardで可視化
tensorboard --logdir=logs

# ブラウザで http://localhost:6006 を開く
```

### 確認すべき指標

1. **curriculum/level** - 現在のカリキュラムレベル（0-5）
2. **curriculum/success_rate** - 現在のレベルでの成功率
3. **reward/phase** - 報酬フェーズ（0-2）
4. **eval/success_rate** - 評価時の成功率

---

## 期待される学習曲線

### Iteration 1-50: Level 0（直線コース）
- Episode Reward: -100 ~ 200
- Success Rate: 0% → 80%
- 行動: ランダム → 前進
- **重要**: ここで学習が進まない場合は基本的な問題あり

### Iteration 50-150: Level 1（単純カーブ）
- Episode Reward: 200 ~ 500
- Success Rate: 0% → 80%
- 行動: 前進 → カーブ

### Iteration 150-400: Level 2（標準楕円）
- Episode Reward: 500 ~ 2000
- Success Rate: 20% → 80%
- 行動: カーブ → チェックポイント通過
- Reward Phase: 0 → 1（フェーズ遷移の可能性）

### Iteration 400-800: Level 3-4（狭い楕円・S字）
- Episode Reward: 2000 ~ 4000
- Success Rate: 30% → 80%
- Reward Phase: 1（探索フェーズ）

### Iteration 800-2000: Level 5（実コース）
- Episode Reward: 3000 ~ 5000
- Success Rate: 10% → 50%+
- Reward Phase: 1 → 2（最適化フェーズへ）
- **最終目標**: Success Rate 50%以上で実機転移可能

---

## カスタマイズ

### カリキュラムの調整

```bash
# Success Rate閾値を下げる（レベルアップしやすく）
python scripts/rl-training/train_adaptive.py \
  --curriculum-success-threshold 0.7

# 最小エピソード数を減らす（早くレベルアップ）
python scripts/rl-training/train_adaptive.py \
  --curriculum-min-episodes 30
```

### 適応的報酬を無効化

```bash
# v3.2の固定係数を使用
python scripts/rl-training/train_adaptive.py \
  --disable-adaptive-reward
```

### ハイパーパラメータ調整

```bash
# 学習率を上げる
python scripts/rl-training/train_adaptive.py \
  --lr 5e-4

# Entropy係数を上げる（探索重視）
python scripts/rl-training/train_adaptive.py \
  --entropy-coef 0.05
```

---

## トラブルシューティング

### Level 0で Success Rate 0% が続く

**原因**: エージェントがまだ前進を学習していない

**対策**:
1. Iteration 50まで待つ
2. 学習率を上げる（`--lr 5e-4`）
3. Entropy係数を上げる（`--entropy-coef 0.05`）

### Level 1以降に進まない

**原因**: Success Rate 80%に到達していない

**対策**:
1. `--curriculum-success-threshold 0.7` で閾値を下げる
2. より長く学習する（`--total-iterations 500`）
3. 報酬係数を確認（TensorBoard）

### Reward Phaseが遷移しない

**原因**: Success Rateが条件を満たしていない

**対策**:
1. カリキュラムレベルを進める（フェーズ遷移はレベルより遅れる）
2. 評価頻度を確認（`--eval-freq 25`）
3. `--disable-adaptive-reward`で固定係数を試す

### 学習が不安定（報酬が激しく変動）

**原因**: 報酬スケールが大きい、またはバッチサイズが小さい

**対策**:
1. Batch sizeを増やす（`--batch-size 128`）
2. Reward clippingを調整（`--reward-clip 5.0`）
3. Max grad normを下げる（`--max-grad-norm 0.3`）

---

## 従来のtrain.pyとの違い

| 機能 | train.py | train_adaptive.py |
|------|----------|-------------------|
| カリキュラム | 手動で`train_curriculum.py` | 自動統合（6レベル） |
| 報酬係数 | 固定（v3.2） | 自動調整（3フェーズ） |
| コース | 1つを指定 | 自動的に変更 |
| 成功判定 | なし | 各レベルで80%目標 |
| 学習安定性 | 不安定（v3.0で崩壊） | 段階的で安定 |

---

## カリキュラムのカスタマイズ

### 新しいレベルの追加

中間レベルを追加したい場合：

1. **コースファイルを作成**
   ```bash
   cd courses/curriculum/
   # 例: Level 1.5を追加
   cp level1_simple_curve.json level1_5_wide_curve.json
   # 内容を編集
   ```

2. **train_adaptive.pyを更新**
   ```python
   curriculum_courses = [
       "courses/curriculum/level0_straight.json",
       "courses/curriculum/level1_simple_curve.json",
       "courses/curriculum/level1_5_wide_curve.json",  # 追加
       "courses/curriculum/level2_simple_oval.json",
       # ...
   ]
   ```

3. **ドキュメントを更新**
   - このドキュメント（ADAPTIVE_TRAINING.md）

### ファイル命名規則

```
level{N}_{コース名}.json

N: レベル番号（0-5）
コース名: 内容を表す簡潔な名前
```

例：
- `level0_straight.json` - Level 0、直線コース
- `level5_real_course.json` - Level 5、実コース

### Level 2-5について

以下のコースは既存ディレクトリからコピーされたものです（元のeasy/medium/hard/は削除済み）：

| カリキュラム | 元ファイル | 備考 |
|-------------|-----------|------|
| level2_simple_oval.json | easy/simple_oval.json（削除済み） | easy難易度 |
| level3_narrow_oval.json | medium/narrow_oval.json（削除済み） | medium難易度 |
| level4_s_curve.json | hard/s_curve.json（削除済み） | hard難易度 |
| level5_real_course.json | real/real-course_course.json | 実コース（参考用に保持） |

**実コースの更新**: courses/real/が更新された場合は、`cp courses/real/real-course_course.json courses/curriculum/level5_real_course.json`でコピー

---

## 次のステップ

### 短期目標
1. Level 4（標準楕円）で Success Rate 80% 達成
2. Reward Phase 2 到達
3. 安定した学習曲線の確認

### 中期目標
1. Level 5（実コース）で Success Rate 50% 達成
2. Domain Randomizationの有効化
3. 実機転移の準備

### 長期目標
1. 並列環境学習の導入（データ収集高速化）
2. Population Based Training（複数モデルの並列学習）
3. 実機でのテスト

---

## 参考

- 報酬設計の詳細: [REWARD_DESIGN.md](REWARD_DESIGN.md)
- カリキュラムマネージャー実装: `src/curriculum/curriculum_manager.py`
- 適応的報酬スケーラー実装: `src/rl/adaptive_reward.py`
- コース定義: `courses/curriculum/level*.json`
