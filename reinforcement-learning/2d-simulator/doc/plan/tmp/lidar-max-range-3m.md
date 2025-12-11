# LiDAR最大距離を3.0mに変更する実装計画

## 概要

LiDARセンサーの最大測定距離を現在の**1.0m**から**3.0m**に変更する。これは実機の中距離センサー（ToF、超音波）の仕様に合わせ、より広い視野を確保しながらも実機転移を考慮した設定。

## 背景と目的

### 現状の問題
- 現在のLiDAR最大距離: **1.0m**（つい先ほど変更したばかり）
- 車体長0.4m → 1.0mは車体長の2.5倍
- 実機で使用予定のセンサー範囲: **0.5〜4.0m程度**

### 3.0mを選択した理由

#### 1.0mとの比較
| 項目 | 1.0m | 3.0m | 評価 |
|------|------|------|------|
| 車体長比 | 2.5倍 | 7.5倍 | ✅ より余裕がある |
| 反応時間（1.0m/s時） | 1.0秒 | 3.0秒 | ✅ 十分な予測時間 |
| 反応時間（2.0m/s時） | 0.5秒 | 1.5秒 | ✅ 高速走行が可能 |
| 計算コスト | 低 | 中 | ✅ 許容範囲 |

#### 速度との兼ね合い
| 速度 | 1.0m時の反応時間 | 3.0m時の反応時間 | 評価 |
|------|------------------|------------------|------|
| 0.5m/s | 2.0秒 | 6.0秒 | 両方OK |
| 1.0m/s | 1.0秒 | 3.0秒 | **3.0mが快適** |
| 1.5m/s | 0.67秒 | 2.0秒 | **3.0mが実用的** |
| 2.0m/s | 0.5秒（ギリギリ） | 1.5秒 | **3.0mなら可能** |
| 3.0m/s | 0.33秒（厳しい） | 1.0秒 | **3.0mならギリギリ** |

#### 実機センサーとの対応
- **VL53L0X** (ToF): 最大2m → 3mは少し長いが許容範囲
- **VL53L1X** (ToF): 最大4m → **3mは良い選択**
- **VL53L4CD** (ToF): 最大1.3m → 3mは長すぎる
- **超音波センサー（HC-SR04）**: 最大4m → **3mは良い選択**
- **赤外線センサー**: 最大0.8-1.5m → 3mは長い

→ **VL53L1Xや超音波センサーを使う場合、3mは最適**

### 1.0mから3.0mへの変更メリット
- ✅ **高速走行が可能**（1.5〜2.0m/s程度まで）
- ✅ **前方の障害物を早期発見**（コーナー予測が向上）
- ✅ **学習の安定性向上**（視野が広いため探索しやすい）
- ✅ **実機の中距離センサーと相性が良い**

### デメリット
- ⚠️ 計算コストが若干増加（レイキャスト距離が3倍）
- ⚠️ 近距離の精度が相対的に低下する可能性（が、1mは十分カバーされる）

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
    max_range: float = 1.0,  # ← 3.0に変更
    angle_min: float = 0.0,
    angle_max: float = 2 * np.pi,
):
```

**影響:**
- デフォルト値が1.0m → 3.0mに変更される
- 既存コードで明示的に`max_range`を指定していない場合は自動的に3.0mになる

#### 1.2 `src/env/minicar_env.py`
**変更箇所（2箇所）:**

**箇所1: `__init__`メソッド (L58-64)**
```python
self.lidar = LiDARSensor(
    self.world.world,
    num_rays=5,
    max_range=1.0,  # ← 3.0に変更
    angle_min=-np.pi/3,
    angle_max=np.pi/3
)
```

**箇所2: `reset`メソッド (L385-391)**
```python
self.lidar = LiDARSensor(
    self.world.world,
    num_rays=5,
    max_range=1.0,  # ← 3.0に変更
    angle_min=-np.pi/3,
    angle_max=np.pi/3
)
```

**影響:**
- 環境の観測空間は変わらない（LiDARの次元数は同じ）
- LiDARの値の範囲が`[0, 1.0]`から`[0, 3.0]`に変化
- 正規化している場合は影響がある可能性

#### 1.3 `tests/test_sensors.py`
**変更箇所（複数箇所）:**

**箇所1: `test_lidar_basic` (L16)**
```python
assert lidar.max_range == 1.0  # ← 3.0に変更
```

**箇所2: `test_lidar_scan_with_wall` (L36, L46)**
```python
# 右側に壁を配置（x=0.5の位置）→ x=2.5に変更
world.add_wall_segment((0.5, -10), (0.5, 10))  # ← (2.5, -10), (2.5, 10)

# 正面方向（0度）は壁まで約0.5m → 約2.5m
assert 0.44 < distances[0] < 0.56  # ← 2.4 < distances[0] < 2.6
```

**箇所3: `test_lidar_scan_with_box` (L57, L63-64)**
```python
# 前方に箱を配置
world.add_static_box(center=(0.5, 0), width=0.2, height=0.2)  # ← (2.0, 0), width=0.4, height=0.4

# 正面方向に箱があるので、距離は約0.4m → 約1.8m
assert distances[0] < 0.5  # ← distances[0] < 2.0
assert distances[0] > 0.3  # ← distances[0] > 1.6
```

**箇所4: `test_lidar_different_orientations` (L72)**
```python
# 右側に壁（x=0.5の位置）→ x=2.5に変更
world.add_wall_segment((0.5, -10), (0.5, 10))  # ← (2.5, -10), (2.5, 10)
```

**箇所5: `test_lidar_range_limits` (L136)**
```python
lidar = LiDARSensor(world.world, num_rays=72, max_range=1.0)  # ← 3.0に変更
```

**影響:**
- テストのアサーションが失敗するため、修正必須
- テストの壁の位置を3.0mの範囲内に調整する必要がある

### 2. 変更が不要なファイル（理由付き）

#### 2.1 `tests/test_env.py`
**理由:**
- 観測空間の次元数は変わらない（LiDAR 5本 + 速度2 + 角速度1 + 前回行動2 = 10次元）
- つい先ほど10次元に修正したばかり
- 値の範囲が変わるだけなので、環境テストには影響しない

#### 2.2 報酬関数 (`src/env/minicar_env.py`)
**現状:**
```python
COLLISION_DISTANCE = 0.22  # 壁衝突とみなす距離（m）
WALL_APPROACH_DISTANCE = 0.3  # 壁接近ペナルティの閾値（m）
```

**理由:**
- 両方とも3.0m以下なので問題なし
- 壁接近ペナルティ（0.3m）は3.0mの範囲内で機能する
- 衝突判定（0.22m）も問題なく動作する

#### 2.3 レンダラー (`src/env/renderer.py`)
**理由:**
- `max_range`への直接的な参照がない
- LiDARの描画は距離データを使って動的に行われる
- 最大距離が変わっても描画ロジックは自動的に対応

#### 2.4 コース定義 (`courses/*.json`)
**理由:**
- コースの定義はメートル単位で記述されている
- LiDARの最大距離とは独立

#### 2.5 PPOアルゴリズム (`src/rl/ppo.py`, `src/rl/trainer.py`)
**理由:**
- 観測空間の次元数は変わらない
- 値の範囲が変わるだけ
- ニューラルネットワークは正規化層で対応可能

### 3. 潜在的な影響（要注意）

#### 3.1 学習済みモデルの互換性 ❌
**影響度: 高**

現在の学習済みモデル（1.0mで訓練）は、3.0mの環境では正しく動作しない可能性が高い。

**理由:**
- ニューラルネットワークの入力分布が変化
- 1.0mで訓練されたモデルは、[0, 1.0]の範囲を前提としている
- 3.0mに変更すると、LiDARの値が[0, 3.0]になり、ネットワークの活性化パターンが変わる

**対策:**
- ✅ **再学習が必要**（推奨）
- または、入力正規化層を追加して対応（複雑）

#### 3.2 観測空間の正規化
**影響度: 中**

現在、観測空間の正規化が行われていないことを確認済み。

**確認項目:**
- `MinicarEnv._get_observation()`でLiDAR値を正規化しているか？→ **していない**
- PPOの入力層で正規化しているか？→ **していない**

**対策:**
- 正規化していない場合 → 影響なし（ただし再学習は必要）
- 将来的に正規化を追加する場合 → 3.0で除算

#### 3.3 報酬のスケール
**影響度: 低**

壁接近ペナルティの計算式:
```python
if min_distance < self.WALL_APPROACH_DISTANCE:
    reward -= (self.WALL_APPROACH_DISTANCE - min_distance) * 10
```

**分析:**
- `WALL_APPROACH_DISTANCE = 0.3`は3.0m以下なので問題なし
- ペナルティのスケールは変わらない
- 再調整は不要

---

## 実装手順

### Phase 1: コード変更

#### ステップ1: `src/env/sensors.py`の修正
```python
# 変更前
max_range: float = 1.0,

# 変更後
max_range: float = 3.0,
```

#### ステップ2: `src/env/minicar_env.py`の修正（2箇所）
```python
# __init__メソッド（L61）
max_range=3.0,

# resetメソッド（L388）
max_range=3.0,
```

#### ステップ3: `tests/test_sensors.py`の修正
```python
# test_lidar_basic（L16）
assert lidar.max_range == 3.0

# test_lidar_scan_with_wall（L36）
world.add_wall_segment((2.5, -10), (2.5, 10))

# test_lidar_scan_with_wall（L46）
assert 2.4 < distances[0] < 2.6

# test_lidar_scan_with_box（L57）
world.add_static_box(center=(2.0, 0), width=0.4, height=0.4)

# test_lidar_scan_with_box（L63-64）
assert distances[0] < 2.0
assert distances[0] > 1.6

# test_lidar_different_orientations（L72）
world.add_wall_segment((2.5, -10), (2.5, 10))

# test_lidar_range_limits（L136）
lidar = LiDARSensor(world.world, num_rays=72, max_range=3.0)
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
grep -rn "normalize\|/ 3\|/3" src/env/minicar_env.py src/rl/ppo.py
```

もし正規化処理が見つかった場合、除数を3.0に変更する。

#### ステップ6: GUI可視化で動作確認
```bash
# 簡単なテスト（100ステップ）
python scripts/rl-training/train.py --total-iterations 1 --gui
```

**確認項目:**
- LiDARの描画が3.0m以内で正しく表示されるか
- 壁までの距離が3.0m以下の範囲で正しく計測されるか
- デバッグ情報の`Min Dist`が妥当な値か（0.22〜3.0の範囲）
- LiDARの線が長く表示されるか（1.0mより長い）

### Phase 3: 再学習

#### ステップ7: 既存モデルの退避
```bash
# 1.0mで訓練したモデルを保存
mkdir -p models/archive/1m-models
cp -r models/checkpoints/* models/archive/1m-models/

# 念のため10.0mのモデルもアーカイブ確認
ls models/archive/10m-models/
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
- 平均速度（3.0mだと高速走行が期待される）

---

## リスク管理

### 高リスク項目

#### R1: 学習が1.0mより遅くなる
**リスク内容:**
- 視野が広すぎて、エージェントが探索に時間をかけすぎる可能性

**対策:**
- エントロピー係数を調整（0.01 → 0.005に下げる）
- 学習率を若干上げる（3e-4 → 5e-4）

**判定基準:**
- 100イテレーション後に成功率が1.0mより低い → ハイパーパラメータ調整

#### R2: 過度に速度を出して衝突する
**リスク内容:**
- 3.0mの視野があるため、エージェントが高速走行を学習し、制御が難しくなる

**対策:**
- 速度報酬を調整（0.1 → 0.05に下げる）
- 壁接近ペナルティを強化（係数10 → 15）

**判定基準:**
- 衝突率が30%を超える → 速度報酬を下げる

### 中リスク項目

#### R3: 計算コストの増加
**リスク内容:**
- レイキャスト距離が3倍になるため、物理シミュレーションが遅くなる可能性

**対策:**
- 学習時のFPSをモニタリング
- 必要に応じてレイ数を削減（5本 → 3本）

#### R4: コースとの整合性
**リスク内容:**
- コースのサイズが3.0mより小さい場合、LiDARが常にmax_rangeを返す

**対策:**
- コースのサイズを確認（`courses/`以下のJSONファイル）
- 小さいコースは使わない、または拡大する

---

## 成功基準

### 必須条件
- ✅ すべてのテストがパスする
- ✅ GUIで3.0mのLiDARが正しく描画される
- ✅ 壁衝突判定が正しく動作する（`min_distance <= 0.22m`）

### 望ましい条件
- ✅ 100イテレーション後に成功率40%以上
- ✅ 500イテレーション後に成功率70%以上
- ✅ 平均速度が1.0m/s以上（1.0m設定より速い）
- ✅ ゴール到達時間が1.0m設定より短い

### 優先度の低い条件
- 学習速度が1.0m時と同等以上
- 計算コストが1.0m時の3倍以内

---

## ロールバック手順

変更を元に戻す必要がある場合：

```bash
# コードを元に戻す（1.0mに）
git checkout src/env/sensors.py src/env/minicar_env.py tests/test_sensors.py

# または、手動で1.0に戻す
# - src/env/sensors.py:45 → max_range: float = 1.0
# - src/env/minicar_env.py:61 → max_range=1.0
# - src/env/minicar_env.py:388 → max_range=1.0
# - tests/test_sensors.py を元に戻す

# 旧モデルを復元
cp -r models/archive/1m-models/* models/checkpoints/
```

---

## 1.0mとの比較

| 項目 | 1.0m | 3.0m | 優位 |
|------|------|------|------|
| 車体長比 | 2.5倍 | 7.5倍 | 3.0m |
| 最高速度（目安） | 1.0m/s | 2.0m/s | 3.0m |
| 反応時間（1.0m/s） | 1.0秒 | 3.0秒 | 3.0m |
| 学習の難易度 | 易しい | 中 | 1.0m |
| 実機転移 | 近距離専用 | 中距離対応 | 3.0m |
| 計算コスト | 低 | 中 | 1.0m |
| コーナー予測 | 直前 | 早期 | 3.0m |

**総合評価:**
- **1.0m**: 安全運転、低速走行、学習が容易
- **3.0m**: 高速走行、早期予測、実用的

---

## 参考情報

### 実機センサーの仕様（参考）

| センサー | 測定範囲 | 精度 | 3.0mとの相性 | 価格帯 |
|---------|---------|------|-------------|--------|
| VL53L0X | 0.03〜2m | ±3% | △（少し長い） | 500円 |
| VL53L1X | 0.04〜4m | ±2% | ✅（最適） | 800円 |
| VL53L4CD | 0.01〜1.3m | ±2% | ✗（3mは対応外） | 700円 |
| HC-SR04（超音波） | 0.02〜4m | ±3mm | ✅（最適） | 200円 |
| GP2Y0A21YK（赤外線） | 0.1〜0.8m | ±5% | ✗（3mは対応外） | 400円 |

**推奨センサー:** VL53L1X または HC-SR04

### 関連ドキュメント
- `doc/plan/tmp/lidar-max-range-1m.md`: 1.0m実装計画（前回作成）
- `doc/plan/tmp/lidar-configuration-research.md`: LiDAR設定の調査
- `doc/plan/tmp/lidar-5rays-plan.md`: 5レイLiDARの実装計画
- `doc/plan/wall_collision_termination.md`: 壁衝突終了条件の実装

---

## 実装チェックリスト

### コード変更
- [ ] `src/env/sensors.py`のデフォルト値を3.0に変更
- [ ] `src/env/minicar_env.py`の`__init__`を修正
- [ ] `src/env/minicar_env.py`の`reset`を修正
- [ ] `tests/test_sensors.py`のアサーションを修正（6箇所）

### 検証
- [ ] `pytest tests/test_sensors.py`がパスする
- [ ] `pytest tests/test_env.py`がパスする
- [ ] GUIで3.0mのLiDAR描画を確認
- [ ] 観測空間の正規化を確認（必要なら修正）

### 再学習
- [ ] 既存モデルを退避（1.0m → archive）
- [ ] 100イテレーションのテスト学習
- [ ] 成功率40%以上を確認
- [ ] 1000イテレーションの本番学習
- [ ] TensorBoardで学習曲線を確認
- [ ] 最終モデルの評価（速度、成功率）

### ドキュメント
- [ ] CLAUDE.mdを更新（LiDAR仕様を3.0mに変更）
- [ ] 学習結果をログに記録
- [ ] 1.0mとの性能比較を記録

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
- LiDARの最大距離を**1.0m → 3.0m**に変更
- 変更箇所は**3ファイル、計9箇所**

### 主な利点
- 高速走行が可能（2.0m/s程度まで）
- 早期の障害物検知（コーナー予測が向上）
- 実機の中距離センサー（VL53L1X、超音波）と相性が良い
- 学習の安定性が向上（視野が広い）

### 主な注意点
- 学習済みモデルは使えない（再学習必須）
- 計算コストが若干増加（レイキャスト距離が3倍）
- 速度が出すぎて衝突するリスクがある（速度報酬の調整が必要かも）

### 1.0mとの使い分け
- **1.0m**: 実機が近距離センサーのみ、安全重視、低速走行
- **3.0m**: 実機が中距離センサー、速度重視、高速走行

### 次のステップ
1. このドキュメントを確認
2. コード変更を実施
3. テストを実行
4. GUIで動作確認
5. 再学習を開始
6. 1.0mとの性能比較
