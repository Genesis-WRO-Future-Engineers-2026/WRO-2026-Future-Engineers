# LiDAR最大距離を1.0mに変更する実装計画

## 概要

LiDARセンサーの最大測定距離を現在の10.0mから**1.0m**に変更する。これは実機の安価なセンサー（ToF、超音波）の仕様に合わせ、sim-to-realのギャップを削減するための変更。

## 背景と目的

### 現状の問題
- シミュレーターのLiDAR最大距離: **10.0m**
- 実機で使用予定のセンサー範囲: **0.5〜2.0m程度**
- シミュレーターと実機のギャップが大きい

### 1.0mを選択した理由
- **60cm（0.6m）との比較**
  - 車体長0.4m → 0.6mは車体長の1.5倍（ギリギリ）
  - 車体長0.4m → 1.0mは車体長の2.5倍（実用的）

- **速度との兼ね合い**
  | 速度 | 0.6m時の反応時間 | 1.0m時の反応時間 | 評価 |
  |------|------------------|------------------|------|
  | 0.5m/s | 1.2秒 | 2.0秒 | 両方OK |
  | 1.0m/s | 0.6秒 | 1.0秒 | **1.0mが実用的** |
  | 1.5m/s | 0.4秒 | 0.67秒 | 1.0mならギリギリ可能 |

- **実機センサーとの対応**
  - VL53L0X (ToF): 最大2m → 1mは現実的
  - VL53L1X (ToF): 最大4m → 1mは保守的
  - 超音波センサー: 0.5-2m → ドンピシャ
  - 赤外線センサー: 0.8-1.5m → ちょうど良い

### 期待される効果
- ✅ 実機とシミュレーターのセンサー仕様が近づく
- ✅ 1m/s前後の実用的な速度で走行可能
- ✅ 学習済みモデルの実機転移が容易になる
- ✅ 計算コストの削減（レイキャスト距離が短くなる）

---

## 影響範囲の分析

### 1. 変更が必要なファイル

#### 1.1 `src/env/sensors.py`
**変更箇所:**
```python
def __init__(
    self,
    world: b2World,
    num_rays: int = 72,
    max_range: float = 10.0,  # ← 1.0に変更
    angle_min: float = 0.0,
    angle_max: float = 2 * np.pi,
):
```

**影響:**
- デフォルト値が変更される
- 既存コードで明示的に`max_range`を指定していない場合は自動的に1.0mになる

#### 1.2 `src/env/minicar_env.py`
**変更箇所（2箇所）:**

**箇所1: `__init__`メソッド (L58-64)**
```python
self.lidar = LiDARSensor(
    self.world.world,
    num_rays=5,
    max_range=10.0,  # ← 1.0に変更
    angle_min=-np.pi/3,
    angle_max=np.pi/3
)
```

**箇所2: `reset`メソッド (L385-391)**
```python
self.lidar = LiDARSensor(
    self.world.world,
    num_rays=5,
    max_range=10.0,  # ← 1.0に変更
    angle_min=-np.pi/3,
    angle_max=np.pi/3
)
```

**影響:**
- 環境の観測空間は変わらない（LiDARの次元数は同じ）
- LiDARの値の範囲が`[0, 10.0]`から`[0, 1.0]`に変化
- 正規化している場合は影響がある可能性

#### 1.3 `tests/test_sensors.py`
**変更箇所（2箇所）:**

**箇所1: `test_lidar_basic` (L16)**
```python
assert lidar.max_range == 10.0  # ← 1.0に変更
```

**箇所2: `test_lidar_range_limits` (L136)**
```python
lidar = LiDARSensor(world.world, num_rays=72, max_range=10.0)  # ← 1.0に変更
```

**影響:**
- テストのアサーションが失敗するため、修正必須
- テストロジック自体は変更不要

### 2. 変更が不要なファイル（理由付き）

#### 2.1 報酬関数 (`src/env/minicar_env.py`)
**現状:**
```python
COLLISION_DISTANCE = 0.22  # 壁衝突とみなす距離（m）
WALL_APPROACH_DISTANCE = 0.3  # 壁接近ペナルティの閾値（m）
```

**理由:**
- 両方とも1.0m以下なので問題なし
- 壁接近ペナルティ（0.3m）は1.0mの範囲内で機能する
- 衝突判定（0.22m）も問題なく動作する

#### 2.2 レンダラー (`src/env/renderer.py`)
**理由:**
- `max_range`への直接的な参照がない
- LiDARの描画は距離データを使って動的に行われる
- 最大距離が変わっても描画ロジックは自動的に対応

#### 2.3 コース定義 (`courses/*.json`)
**理由:**
- コースの定義はメートル単位で記述されている
- LiDARの最大距離とは独立

#### 2.4 PPOアルゴリズム (`src/rl/ppo.py`, `src/rl/trainer.py`)
**理由:**
- 観測空間の次元数は変わらない
- 値の範囲が変わるだけ
- ニューラルネットワークは正規化層で対応可能

### 3. 潜在的な影響（要注意）

#### 3.1 学習済みモデルの互換性 ❌
**影響度: 高**

現在の学習済みモデル（10.0mで訓練）は、1.0mの環境では正しく動作しない可能性が高い。

**理由:**
- ニューラルネットワークの入力分布が変化
- 10.0mで訓練されたモデルは、[0, 10.0]の範囲を前提としている
- 1.0mに変更すると、LiDARの値が[0, 1.0]になり、ネットワークの活性化パターンが変わる

**対策:**
- ✅ **再学習が必要**（推奨）
- または、入力正規化層を追加して対応（複雑）

#### 3.2 観測空間の正規化
**影響度: 中**

現在、観測空間の正規化が行われているか確認が必要。

**確認項目:**
- `MinicarEnv._get_observation()`でLiDAR値を正規化しているか？
- PPOの入力層で正規化しているか？

**調査方法:**
```bash
# 正規化処理を探す
grep -rn "normalize\|/.*max_range\|/ 10" src/env/minicar_env.py src/rl/
```

**対策:**
- 正規化している場合 → 除数を10.0から1.0に変更
- 正規化していない場合 → 影響なし（ただし再学習は必要）

#### 3.3 報酬のスケール
**影響度: 低**

壁接近ペナルティの計算式:
```python
if min_distance < self.WALL_APPROACH_DISTANCE:
    reward -= (self.WALL_APPROACH_DISTANCE - min_distance) * 10
```

**分析:**
- `WALL_APPROACH_DISTANCE = 0.3`は1.0m以下なので問題なし
- ペナルティのスケールは変わらない
- 再調整は不要

---

## 実装手順

### Phase 1: コード変更

#### ステップ1: `src/env/sensors.py`の修正
```python
# 変更前
max_range: float = 10.0,

# 変更後
max_range: float = 1.0,
```

#### ステップ2: `src/env/minicar_env.py`の修正（2箇所）
```python
# __init__メソッド（L61）
max_range=1.0,

# resetメソッド（L388）
max_range=1.0,
```

#### ステップ3: `tests/test_sensors.py`の修正（2箇所）
```python
# test_lidar_basic（L16）
assert lidar.max_range == 1.0

# test_lidar_range_limits（L136）
lidar = LiDARSensor(world.world, num_rays=72, max_range=1.0)
```

### Phase 2: 検証

#### ステップ4: テスト実行
```bash
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

# センサーテスト
pytest tests/test_sensors.py -v

# 環境テスト
pytest tests/test_env.py -v

# 全テスト
pytest tests/ -v
```

#### ステップ5: 観測空間の正規化確認
```bash
# 正規化処理を探す
grep -rn "normalize\|/ 10\|/10" src/env/minicar_env.py src/rl/ppo.py
```

もし正規化処理が見つかった場合、除数を1.0に変更する。

#### ステップ6: GUI可視化で動作確認
```bash
# 簡単なテスト（100ステップ）
python scripts/rl-training/train.py --total-iterations 1 --gui
```

**確認項目:**
- LiDARの描画が1.0m以内で正しく表示されるか
- 壁までの距離が1.0m以下の範囲で正しく計測されるか
- デバッグ情報の`Min Dist`が妥当な値か（0.22〜1.0の範囲）

### Phase 3: 再学習

#### ステップ7: 既存モデルの退避
```bash
# 10.0mで訓練したモデルを保存
mkdir -p models/archive/10m-models
cp -r models/checkpoints/* models/archive/10m-models/
```

#### ステップ8: 新規学習の実行
```bash
# 短時間テスト（100イテレーション）
python scripts/rl-training/train.py --total-iterations 100 --gui

# 本番学習（1000イテレーション、GUIなし）
python scripts/rl-training/train.py --total-iterations 1000
```

#### ステップ9: 学習結果の評価
```bash
# TensorBoardで学習曲線を確認
tensorboard --logdir=logs

# 学習済みモデルをテスト
python scripts/rl-training/test_saved_model.py --model models/checkpoints/final_model.pth
```

**評価指標:**
- 成功率（ゴール到達率）
- 平均報酬
- 平均エピソード長
- 壁接近頻度

---

## リスク管理

### 高リスク項目

#### R1: 学習が収束しない
**リスク内容:**
- 1.0mだと視野が狭すぎて、学習が進まない可能性

**対策:**
- 段階的なカリキュラム学習を使用
  1. 最初は2.0mで学習
  2. 成功率80%で1.5mに移行
  3. 最終的に1.0mに移行
- または、報酬関数を調整（速度報酬を下げる）

**判定基準:**
- 100イテレーション後に成功率が10%未満 → カリキュラム学習を検討

#### R2: 衝突頻度が増加
**リスク内容:**
- 視野が狭くなり、壁衝突が増える

**対策:**
- `WALL_APPROACH_DISTANCE`を0.4mに増やす（0.3m → 0.4m）
- 壁接近ペナルティの係数を増やす（10 → 15）

**判定基準:**
- 衝突率が50%を超える → ペナルティを調整

### 中リスク項目

#### R3: コース設計との不整合
**リスク内容:**
- 既存コースが1.0mの視野では難しすぎる可能性

**対策:**
- 簡単なコース（`courses/simple_straight.json`など）から始める
- 複雑なコースは後回し

#### R4: 速度が出せない
**リスク内容:**
- 安全マージンのため、速度が遅くなる

**対策:**
- これは想定内の挙動
- 実機でも安全運転が優先されるため、許容範囲

---

## 成功基準

### 必須条件
- ✅ すべてのテストがパスする
- ✅ GUIで1.0mのLiDARが正しく描画される
- ✅ 壁衝突判定が正しく動作する（`min_distance <= 0.22m`）

### 望ましい条件
- ✅ 100イテレーション後に成功率30%以上
- ✅ 500イテレーション後に成功率60%以上
- ✅ 平均速度が0.5m/s以上
- ✅ 壁接近ペナルティの発動頻度が適切（過度でない）

### 優先度の低い条件
- ゴール到達時間が10.0m時と同等
- 報酬の絶対値が10.0m時と同等

---

## ロールバック手順

変更を元に戻す必要がある場合：

```bash
# コードを元に戻す
git checkout src/env/sensors.py src/env/minicar_env.py tests/test_sensors.py

# または、手動で10.0に戻す
# - src/env/sensors.py:45 → max_range: float = 10.0
# - src/env/minicar_env.py:61 → max_range=10.0
# - src/env/minicar_env.py:388 → max_range=10.0
# - tests/test_sensors.py:16 → assert lidar.max_range == 10.0
# - tests/test_sensors.py:136 → max_range=10.0

# 旧モデルを復元
cp -r models/archive/10m-models/* models/checkpoints/
```

---

## 参考情報

### 実機センサーの仕様（参考）

| センサー | 測定範囲 | 精度 | 価格帯 |
|---------|---------|------|--------|
| VL53L0X | 0.03〜2m | ±3% | 500円 |
| VL53L1X | 0.04〜4m | ±2% | 800円 |
| HC-SR04（超音波） | 0.02〜4m | ±3mm | 200円 |
| GP2Y0A21YK（赤外線） | 0.1〜0.8m | ±5% | 400円 |

### 関連ドキュメント
- `doc/plan/tmp/lidar-configuration-research.md`: LiDAR設定の調査
- `doc/plan/tmp/lidar-5rays-plan.md`: 5レイLiDARの実装計画
- `doc/plan/wall_collision_termination.md`: 壁衝突終了条件の実装

---

## 実装チェックリスト

### コード変更
- [ ] `src/env/sensors.py`のデフォルト値を1.0に変更
- [ ] `src/env/minicar_env.py`の`__init__`を修正
- [ ] `src/env/minicar_env.py`の`reset`を修正
- [ ] `tests/test_sensors.py`のアサーションを修正（2箇所）

### 検証
- [ ] `pytest tests/test_sensors.py`がパスする
- [ ] `pytest tests/test_env.py`がパスする
- [ ] GUIで1.0mのLiDAR描画を確認
- [ ] 観測空間の正規化を確認（必要なら修正）

### 再学習
- [ ] 既存モデルを退避
- [ ] 100イテレーションのテスト学習
- [ ] 成功率30%以上を確認
- [ ] 1000イテレーションの本番学習
- [ ] TensorBoardで学習曲線を確認
- [ ] 最終モデルの評価

### ドキュメント
- [ ] CLAUDE.mdを更新（LiDAR仕様を1.0mに変更）
- [ ] 学習結果をログに記録

---

## タイムライン（推定）

| フェーズ | 作業内容 | 所要時間 |
|---------|---------|---------|
| Phase 1 | コード変更 | 10分 |
| Phase 2 | テスト・検証 | 20分 |
| Phase 3 | 再学習（100iter） | 30分 |
| Phase 3 | 再学習（1000iter） | 5時間 |
| Phase 3 | 評価・調整 | 1時間 |
| **合計** | | **約7時間** |

---

## まとめ

### 変更内容
- LiDARの最大距離を**10.0m → 1.0m**に変更
- 変更箇所は**4ファイル、計6箇所**

### 主な利点
- 実機センサーとの仕様が近づく
- 1m/s前後の実用的な速度で走行可能
- sim-to-realのギャップ削減

### 主な注意点
- 学習済みモデルは使えない（再学習必須）
- 視野が狭くなるため、学習が難しくなる可能性
- カリキュラム学習の導入を検討

### 次のステップ
1. このドキュメントを確認
2. コード変更を実施
3. テストを実行
4. GUIで動作確認
5. 再学習を開始
