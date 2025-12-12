# Sim2Real対応: 観測空間を10次元に戻す実装計画

## 概要

本番環境（6分間連続周回レース）では物理的なチェックポイントを設置できないため、観測空間に含まれるチェックポイント情報（距離・角度）が使用できない。

学習時と本番時の観測空間を一致させるため、**観測空間を12次元から10次元に戻す**。

---

## 問題の整理

### 現状（12次元観測空間）

```python
[
    lidar_scan,              # 5次元
    velocity,                # 2次元
    angular_velocity,        # 1次元
    last_action,             # 2次元
    checkpoint_distance,     # 1次元 ← 本番で取得不可
    checkpoint_angle,        # 1次元 ← 本番で取得不可
]
```

### 問題点

- **学習環境**: チェックポイント情報あり（12次元）
- **本番環境**: チェックポイント情報なし（10次元のみ）
- **結果**: 観測空間の不一致により、学習済みモデルが使用不可

---

## 解決方針

### 新しい観測空間（10次元）

```python
[
    lidar_scan,        # 5次元（前方120度の壁までの距離）
    velocity,          # 2次元（vx, vy）
    angular_velocity,  # 1次元
    last_action,       # 2次元（steering, throttle）
]
```

### 学習の仕組み

1. **チェックポイント**: 学習時のみ使用（報酬計算・進捗管理）
2. **観測空間**: チェックポイント情報を含めない
3. **エージェント**: LiDARと速度だけで走行を学習
4. **本番環境**: 学習済みモデルをそのまま使用

### 報酬設計（変更なし）

```python
# 速度報酬
reward += speed * 0.05

# 時間ペナルティ
reward -= 0.3

# 壁接近ペナルティ
if min_distance < 0.3:
    reward -= (0.3 - min_distance) * 10

# 衝突ペナルティ
if collision:
    reward += -100.0

# チェックポイント報酬（学習補助）
if checkpoint_passed:
    reward += 100.0

# ゴール報酬
if goal_reached:
    reward += 500.0
    # 時間ボーナス
    reward += (max_steps - current_step) * 1.5
```

**重要**: チェックポイント報酬は学習時の補助として使用。エージェントは観測空間にチェックポイント情報がないため、LiDARで壁を認識しながらコースを走ることを学習する。

---

## 実装手順

### Phase 1: 観測空間を10次元に戻す

#### 1.1 `minicar_env.py`の修正

**ファイル**: `src/env/minicar_env.py`

**変更箇所1**: `observation_space`の定義（`__init__`メソッド）

```python
# 観測空間: LiDAR(5) + velocity(2) + angular_velocity(1) + last_action(2) = 10
self.observation_space = spaces.Box(
    low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32  # 12 → 10
)
```

**変更箇所2**: `_get_observation()`メソッド

```python
def _get_observation(self) -> np.ndarray:
    """
    現在の観測を取得

    Returns:
        観測ベクトル (10次元)  # 12 → 10
    """
    # キャッシュされたデータを使用
    lidar_scan = self._cached_lidar_scan
    velocity = np.array(self._cached_vehicle_state["velocity"])
    angular_velocity = np.array([self._cached_vehicle_state["angular_velocity"]])

    # チェックポイント情報は削除（観測空間に含めない）
    # NOTE: チェックポイントは報酬計算でのみ使用

    # 観測を結合
    obs = np.concatenate([
        lidar_scan,              # 5
        velocity,                # 2
        angular_velocity,        # 1
        self.last_action,        # 2
        # checkpoint_distance と checkpoint_angle は削除
    ])

    return obs.astype(np.float32)
```

**変更箇所3**: `_get_next_checkpoint_info()`メソッドの扱い

このメソッドは残す（報酬計算で使用するため）が、観測空間には含めない。

---

### Phase 2: テストを更新

#### 2.1 `test_env.py`の修正

**ファイル**: `tests/test_env.py`

**変更箇所**: すべての観測空間サイズのアサーション

```python
# 10次元 ← 12次元から変更
assert obs.shape == (10,)
```

**影響を受けるテスト**:
- `test_env_reset()` (line 20)
- `test_env_step()` (line 36)
- `test_observation_space()` (line 62)
- `test_observation_bounds()` (line 162以降)

#### 2.2 `test_checkpoint_observation.py`の削除または無効化

**ファイル**: `tests/test_checkpoint_observation.py`

このテストファイルは12次元観測空間（チェックポイント情報を含む）を前提としているため、以下のいずれかを実行:

**オプション1**: ファイルを削除
```bash
rm tests/test_checkpoint_observation.py
```

**オプション2**: テストをスキップ（将来の参考のため残す）
```python
import pytest

@pytest.mark.skip(reason="観測空間から削除（Sim2Real対応）")
def test_checkpoint_distance_calculation():
    ...
```

---

### Phase 3: ドキュメント更新

#### 3.1 `CLAUDE.md`の修正

**ファイル**: `CLAUDE.md`

**変更箇所**: 観測空間の説明

```markdown
### 観測空間構成 (10次元)

- LiDAR: 5次元（前方120度を5方向でカバー: -60° ~ +60°）
- 速度: 2次元（vx, vy）
- 角速度: 1次元
- 前回の行動: 2次元（steering, throttle）

**Sim2Real対応**:
- チェックポイント情報は観測空間に含めない
- 学習時はチェックポイントを報酬計算に使用（進捗管理）
- 本番時はLiDARと速度情報のみで周回走行
```

#### 3.2 実装計画書の更新

**ファイル**: `doc/plan/tmp/checkpoint-observation-implementation-plan.md`

このファイルは古くなったため、アーカイブまたは削除:

```bash
mv doc/plan/tmp/checkpoint-observation-implementation-plan.md \
   doc/plan/archive/checkpoint-observation-implementation-plan.md.old
```

---

## 本番コースデータの作成

### コースJSON作成方法

本番コースが決まっている場合、以下の手順でデータ化:

#### 1. コース形状の測定

実際のコースを測定して以下の情報を取得:
- 壁の座標（ポリゴンの頂点）
- スタート位置と角度
- コース幅
- コース全長

#### 2. JSONファイル作成

`courses/competition/real_course.json`として作成:

```json
{
  "name": "本番コース",
  "start_position": [0.0, 0.0],
  "start_angle": 0.0,
  "goal_position": [0.0, 0.0],
  "goal_radius": 1.0,
  "walls": [
    {
      "type": "polygon",
      "vertices": [
        [x1, y1],
        [x2, y2],
        [x3, y3],
        ...
      ]
    }
  ],
  "checkpoints": [
    {
      "position": [x, y],
      "radius": 1.5,
      "index": 0
    },
    ...
  ]
}
```

**注意**:
- `goal_position`はスタート位置と同じ（周回コース）
- `checkpoints`は学習補助のため、コース上に適度に配置
- 壁の座標は実際のコースの縮尺に合わせる（例: 1m = 1単位）

#### 3. 学習での使用

```python
env = MinicarEnv(course_file="courses/competition/real_course.json")
```

カリキュラム学習の最終レベルとして設定可能。

---

## 期待される効果

### 1. Sim2Real対応

- ✅ 学習時と本番時の観測空間が一致（10次元）
- ✅ 学習済みモデルをそのまま本番環境で使用可能
- ✅ チェックポイント不要で周回走行可能

### 2. 学習効率

- ⚠️ 12次元→10次元により、学習が若干難しくなる可能性
- ✅ ただし、LiDARだけで走行できれば汎用性が高い
- ✅ 本番コースでの学習により、コース特化の最適化

### 3. 本番パフォーマンス

- ✅ 6分間連続周回に対応
- ✅ 最速ラップタイムを出すための走行を学習
- ✅ 衝突回避とスピードのバランスを獲得

---

## リスクと対策

### リスク1: チェックポイント情報なしで学習が困難

**問題**:
- ゴールの方向が分からず、エージェントが迷走する可能性
- 学習時間が大幅に増加する可能性

**対策**:
1. **段階的学習**:
   - まず簡単なコース（simple_oval）で基本走行を学習
   - その後、本番コースで転移学習
2. **報酬シェーピング強化**:
   - チェックポイント報酬を維持（学習補助）
   - 壁に沿って走る報酬を追加検討
3. **LiDAR方向数の増加**:
   - 必要に応じて5方向→7方向に増やす（前方+側方カバー）

### リスク2: 本番コースが複雑で学習が収束しない

**問題**:
- 本番コースがsimple_ovalより複雑な場合、学習が困難

**対策**:
1. **カリキュラム学習の継続**:
   ```
   Level 0: simple_oval (易)
   Level 1: narrow_oval (中)
   Level 2: tight_oval (難)
   Level 3: real_course (本番) ← 追加
   ```
2. **学習ステップ数の増加**:
   - `total_iterations`を200→500に増やす
   - `n_steps`を2048→4096に増やす

### リスク3: 本番環境との物理特性の違い

**問題**:
- シミュレーションと実機で車両の挙動が異なる

**対策**:
1. **Domain Randomization（将来実装）**:
   - 摩擦係数、質量、センサーノイズをランダム化
   - シミュレーションの多様性を増やす
2. **実機でのファインチューニング**:
   - 実機データを収集し、追加学習

---

## 実装完了の定義

- [ ] Phase 1: 観測空間を10次元に戻す
- [ ] Phase 2: テストを更新し、全テスト通過
- [ ] Phase 3: ドキュメントを更新
- [ ] 短時間学習で動作確認（エラーなし）
- [ ] 本番コースJSONの作成方法を確立
- [ ] 本番コースでの学習実験

---

## 次のステップ

### 即座に実行

1. **Phase 1-3の実装**（観測空間の変更）
2. **テスト実行**（全テスト通過確認）
3. **短時間学習**（5イテレーション）で動作確認

### 本番コース準備

4. **本番コースの測定**
5. **JSONファイル作成**
6. **本番コースでの学習開始**

---

**作成日**: 2025-12-12
**場所**: `doc/plan/sim2real-observation-space-fix.md`
