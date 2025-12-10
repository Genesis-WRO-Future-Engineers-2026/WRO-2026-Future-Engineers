# 車両サイズの重複定義解消 - 実装計画書

**作成日:** 2025-12-10
**優先度:** 🟡 高優先度2
**推定作業時間:** 30分
**実装難易度:** ⭐☆☆☆☆ (低)
**関連ドキュメント:** [env リファクタリング計画書](../README.md)

---

## 📋 目次

1. [問題の概要](#問題の概要)
2. [現状分析](#現状分析)
3. [解決方針](#解決方針)
4. [詳細な実装手順](#詳細な実装手順)
5. [テスト計画](#テスト計画)
6. [リスク分析](#リスク分析)
7. [チェックリスト](#チェックリスト)

---

## 問題の概要

### 問題の説明

車両のサイズ（幅・長さ）が以下の2つのファイルでハードコードされており、DRY原則に違反しています:

```python
# vehicle.py:26-27
self.width = 0.2   # m
self.length = 0.4  # m

# renderer.py:124-125
length = 0.4  # m
width = 0.2   # m
```

### 問題点

1. **DRY原則違反**: 同じ値が2箇所に重複定義されている
2. **保守性の低下**: 片方を変更してももう片方を変更し忘れるリスク
3. **潜在的なバグ**: 値がずれると描画と物理が一致しなくなる
4. **拡張性の欠如**: 異なるサイズの車両を扱いづらい

### 期待される効果

- ✅ **保守性向上**: 車両サイズの変更が1箇所で完結
- ✅ **バグ防止**: 物理と描画のサイズ不一致を防止
- ✅ **DRY原則の実践**: コードの重複を排除
- ✅ **拡張性向上**: 将来的に異なるサイズの車両を扱いやすくなる

---

## 現状分析

### 影響範囲の調査

#### 1. `vehicle.py` - 車両の物理モデル

```python
class Vehicle:
    def __init__(self, world: b2World, start_pos: Tuple[float, float], start_angle: float = 0.0):
        # 車両パラメータ
        self.width = 0.2  # m (行26)
        self.length = 0.4  # m (行27)

        # ... 以下で使用される箇所 ...

        # ボディの形状作成 (行44-48)
        self.body.CreatePolygonFixture(
            box=(self.length / 2, self.width / 2),
            density=self.mass / (self.length * self.width),
            friction=0.7,
        )
```

**使用箇所:**
- 行44-48: Box2Dの物理ボディの形状定義に使用

#### 2. `renderer.py` - 描画処理

```python
class Renderer:
    def draw_vehicle(self, position: Tuple[float, float], angle: float):
        """車両を描画"""
        # 車両のサイズ (行124-125)
        length = 0.4  # m
        width = 0.2   # m

        # ... 以下で使用される箇所 ...

        # 車両の4隅の計算 (行128-135)
        half_l = length / 2
        half_w = width / 2
        corners = [
            (half_l, half_w),
            (-half_l, half_w),
            (-half_l, -half_w),
            (half_l, -half_w),
        ]

        # 前方向を示す線の描画 (行156-162)
        front_x = position[0] + half_l * cos_a
        front_y = position[1] + half_l * sin_a
```

**使用箇所:**
- 行128-135: 車両の4隅の座標計算
- 行156-162: 前方向を示す線の描画

#### 3. `minicar_env.py` - 環境クラス

```python
class MinicarEnv(gym.Env):
    def render(self):
        # ... (省略) ...

        # 車両描画の呼び出し (行309)
        self.renderer.draw_vehicle(state["position"], state["angle"])
```

**現在の呼び出し方:**
- 位置と角度のみを渡している
- 車両オブジェクト自体は渡していない

---

## 解決方針

### 設計の選択肢

#### オプション1: ゲッターメソッドを追加（最小限の変更）

**メリット:**
- 既存の`draw_vehicle`のシグネチャを変更しない
- 変更が最小限

**デメリット:**
- サイズ情報を別途取得して渡す必要がある
- 将来的な拡張性が低い

```python
# vehicle.py
def get_dimensions(self) -> Tuple[float, float]:
    return self.length, self.width

# renderer.py
def draw_vehicle(self, position: Tuple[float, float], angle: float, dimensions: Tuple[float, float]):
    length, width = dimensions
    # ...
```

#### オプション2: 車両オブジェクトを渡す（推奨）★

**メリット:**
- より良いカプセル化
- 将来的に他の車両情報も簡単に取得できる
- 呼び出し側のコードがシンプルになる
- 車両の状態と描画が密結合される

**デメリット:**
- `draw_vehicle`のシグネチャが変わる
- 既存の呼び出し箇所を修正する必要がある

```python
# renderer.py
def draw_vehicle(self, vehicle: Vehicle):
    state = vehicle.get_state()
    position = state["position"]
    angle = state["angle"]
    length, width = vehicle.length, vehicle.width
    # ...

# minicar_env.py
self.renderer.draw_vehicle(self.vehicle)
```

### 採用する方針: **オプション2（推奨）**

**理由:**
1. **カプセル化の改善**: 車両の情報は車両オブジェクトが持つべき
2. **呼び出し側の簡潔化**: `minicar_env.py`のコードがシンプルになる
3. **将来の拡張性**: 色、タイプなど他の車両情報も簡単に追加できる
4. **一貫性**: 他の描画メソッド（`draw_lidar`など）も同様のパターンに統一可能

---

## 詳細な実装手順

### ステップ1: `vehicle.py` の修正

**目的**: サイズ情報へのアクセスを明示的にする（既にpublicフィールドなので変更不要）

**変更内容**: なし（`self.width`と`self.length`は既にpublicフィールドとして定義されている）

**確認事項**:
- ✅ `self.width`と`self.length`がpublicフィールドとして定義されている
- ✅ コンストラクタで初期化されている

```python
# vehicle.py (変更なし)
class Vehicle:
    def __init__(self, world: b2World, start_pos: Tuple[float, float], start_angle: float = 0.0):
        # 車両パラメータ
        self.width = 0.2  # m
        self.length = 0.4  # m
        # ... (以下変更なし)
```

---

### ステップ2: `renderer.py` の修正

**目的**: `draw_vehicle`メソッドのシグネチャを変更し、車両オブジェクトから直接サイズを取得する

#### 2.1. インポートの追加

```python
# renderer.py の先頭付近
from typing import Tuple, List, Optional, TYPE_CHECKING

# 循環インポートを防ぐため
if TYPE_CHECKING:
    from src.env.vehicle import Vehicle
```

**理由**: 型ヒントのために`Vehicle`クラスをインポートする必要があるが、実行時の循環インポートを防ぐため`TYPE_CHECKING`を使用

#### 2.2. `draw_vehicle`メソッドの変更

**変更前:**

```python
def draw_vehicle(self, position: Tuple[float, float], angle: float):
    """
    車両を描画

    Args:
        position: 車両の位置 (x, y) (m)
        angle: 車両の角度 (rad)
    """
    # 車両のサイズ
    length = 0.4  # m
    width = 0.2  # m

    # 車両の4隅の座標（ローカル座標）
    half_l = length / 2
    half_w = width / 2
    # ... (以下省略)
```

**変更後:**

```python
def draw_vehicle(self, vehicle: "Vehicle"):
    """
    車両を描画

    Args:
        vehicle: 描画する車両オブジェクト
    """
    # 車両の状態を取得
    state = vehicle.get_state()
    position = state["position"]
    angle = state["angle"]

    # 車両のサイズを取得（Vehicleオブジェクトから）
    length = vehicle.length
    width = vehicle.width

    # 車両の4隅の座標（ローカル座標）
    half_l = length / 2
    half_w = width / 2
    # ... (以下変更なし)
```

**変更のポイント:**
1. **シグネチャの変更**: `position`と`angle`を`vehicle`に統一
2. **状態の取得**: `vehicle.get_state()`で位置と角度を取得
3. **サイズの取得**: `vehicle.length`と`vehicle.width`を使用
4. **ロジックは変更なし**: 以降の描画ロジックは全く同じ

---

### ステップ3: `minicar_env.py` の修正

**目的**: `draw_vehicle`の呼び出しを新しいシグネチャに合わせる

**変更箇所**: `render()`メソッド内

**変更前:**

```python
# minicar_env.py の render() メソッド内（行309付近）
state = self.vehicle.get_state()
# ... (省略)
self.renderer.draw_vehicle(state["position"], state["angle"])
```

**変更後:**

```python
# minicar_env.py の render() メソッド内
# 状態取得は他の目的で必要な場合のみ残す
self.renderer.draw_vehicle(self.vehicle)
```

**変更のポイント:**
1. **呼び出しの簡潔化**: 車両オブジェクトのみを渡す
2. **重複の削減**: `get_state()`の呼び出しが描画側に移動（必要な場合のみ）

---

### ステップ4: コード全体の確認

#### 4.1. 他の呼び出し箇所の確認

```bash
# draw_vehicle の呼び出し箇所を検索
grep -rn "draw_vehicle" src/
```

**確認結果**:
- `minicar_env.py:309` のみが呼び出し箇所

#### 4.2. テストコードの確認

```bash
# テストコード内での使用を確認
grep -rn "draw_vehicle" tests/
```

**確認事項**:
- テストコードで`draw_vehicle`を直接呼んでいる箇所があるか確認
- ある場合は同様に修正

---

## テスト計画

### 1. ユニットテスト（自動）

#### テスト1: 車両サイズの取得

```python
# tests/test_vehicle.py に追加
def test_vehicle_dimensions():
    """車両のサイズが正しく設定されているか"""
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    assert vehicle.width == 0.2
    assert vehicle.length == 0.4
```

#### テスト2: 描画メソッドの呼び出し

```python
# tests/test_renderer.py に追加（または新規作成）
def test_draw_vehicle_with_vehicle_object():
    """draw_vehicleが車両オブジェクトを受け取れるか"""
    renderer = Renderer(screen_width=800, screen_height=600)
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 例外が発生しないことを確認
    try:
        renderer.draw_vehicle(vehicle)
        # Pygame初期化が必要なため、実際の描画テストは統合テストで行う
    except TypeError as e:
        pytest.fail(f"draw_vehicle should accept Vehicle object: {e}")
    finally:
        renderer.close()
```

#### テスト3: 統合テスト（環境全体）

```python
# tests/test_env.py に追加
def test_render_with_new_signature():
    """新しいdraw_vehicleシグネチャで環境が正しく動作するか"""
    env = MinicarEnv(render_mode="rgb_array")
    env.reset()

    # 1ステップ実行してレンダリング
    action = env.action_space.sample()
    _, _, _, _, _ = env.step(action)

    # レンダリングが成功することを確認
    frame = env.render()
    assert frame is not None
    assert frame.shape == (600, 800, 3)  # デフォルトの画面サイズ

    env.close()
```

---

### 2. 手動テスト（ビジュアル確認）

#### テスト1: シミュレーターの起動

```bash
# シミュレーターを起動して車両が正しく描画されるか確認
cd scripts/simulator-demo
python manual_control.py
```

**確認項目:**
- ✅ 車両が正しく表示される
- ✅ 車両のサイズが以前と同じ（見た目に変化がない）
- ✅ 車両が壁と正しく衝突する（物理と描画のサイズが一致している）
- ✅ 前方向を示す線が正しい位置に表示される

#### テスト2: 異なるサイズの車両でテスト

```python
# vehicle.py で一時的にサイズを変更してテスト
self.width = 0.3  # 元: 0.2
self.length = 0.5  # 元: 0.4
```

**手順:**
1. 上記の値を変更
2. シミュレーターを起動
3. 車両が大きく表示されることを確認
4. 物理的な挙動（衝突判定）も大きくなっていることを確認
5. 元の値に戻す

**期待結果:**
- 描画と物理の両方が新しいサイズで動作する
- 1箇所の変更で両方が更新される

---

### 3. パフォーマンステスト

#### テスト: レンダリング速度の確認

```python
# パフォーマンスに影響がないことを確認
import time

env = MinicarEnv(render_mode="rgb_array")
env.reset()

start_time = time.time()
for _ in range(1000):
    action = env.action_space.sample()
    env.step(action)
    env.render()
end_time = time.time()

fps = 1000 / (end_time - start_time)
print(f"Average FPS: {fps:.2f}")
# 変更前後で大きな差がないことを確認（±5%以内が目安）
```

---

## リスク分析

### 高リスク（発生確率: 低、影響度: 大）

| リスク | 影響 | 対策 |
|--------|------|------|
| 型ヒントの循環インポートエラー | ランタイムエラー | `TYPE_CHECKING`を使用して実行時のインポートを防ぐ |

### 中リスク（発生確率: 中、影響度: 中）

| リスク | 影響 | 対策 |
|--------|------|------|
| テストコードでの直接呼び出しがある | テストが失敗する | 事前にgrepで全検索し、すべての呼び出し箇所を修正 |
| 他のスクリプトでRendererを直接使用している | スクリプトが動作しなくなる | scriptsディレクトリ全体を検索し、必要に応じて修正 |

### 低リスク（発生確率: 低、影響度: 小）

| リスク | 影響 | 対策 |
|--------|------|------|
| パフォーマンスへの影響 | 若干の速度低下 | `get_state()`は軽量な操作なので影響は無視できる |

---

## チェックリスト

### 実装前の準備

- [ ] 現在のブランチを確認（`feat/kamite`など適切なブランチにいるか）
- [ ] 現状のコードをバックアップ（コミット）
- [ ] 影響範囲を把握（`grep`で全検索）
- [ ] テスト環境の準備（仮想環境の有効化、依存関係の確認）

### ステップ1: `vehicle.py`

- [ ] ファイルを確認（変更不要だが念のため）
- [ ] `self.width`と`self.length`がpublicフィールドとして定義されていることを確認

### ステップ2: `renderer.py`

- [ ] `TYPE_CHECKING`のインポートを追加
- [ ] `Vehicle`の型インポートを追加（`if TYPE_CHECKING`ブロック内）
- [ ] `draw_vehicle`のシグネチャを変更
  - [ ] 引数を`vehicle: "Vehicle"`に変更
  - [ ] docstringを更新
- [ ] `draw_vehicle`の実装を修正
  - [ ] `vehicle.get_state()`で位置と角度を取得
  - [ ] `vehicle.length`と`vehicle.width`でサイズを取得
  - [ ] ハードコードされた`length = 0.4`と`width = 0.2`を削除
- [ ] コードの整合性を確認

### ステップ3: `minicar_env.py`

- [ ] `render()`メソッド内の呼び出しを修正
  - [ ] `self.renderer.draw_vehicle(state["position"], state["angle"])`を削除
  - [ ] `self.renderer.draw_vehicle(self.vehicle)`に変更
- [ ] 不要な`get_state()`呼び出しがあれば整理（他の目的で使用していない場合）

### ステップ4: 他の箇所の確認

- [ ] `grep -rn "draw_vehicle" src/`で他の呼び出し箇所を確認
- [ ] `grep -rn "draw_vehicle" tests/`でテストコードを確認
- [ ] `grep -rn "draw_vehicle" scripts/`でスクリプトを確認
- [ ] 見つかった箇所をすべて修正

### テスト

#### 自動テスト
- [ ] 既存のユニットテストを実行（`pytest tests/test_vehicle.py`）
- [ ] 既存の統合テストを実行（`pytest tests/test_env.py`）
- [ ] 新しいテストを追加（必要に応じて）
- [ ] 全テストが成功することを確認（`pytest tests/`）

#### 手動テスト
- [ ] シミュレーターを起動（`python scripts/simulator-demo/manual_control.py`）
- [ ] 車両が正しく表示されることを確認
- [ ] 車両のサイズが以前と同じことを確認
- [ ] 車両の動きに異常がないことを確認
- [ ] LiDARスキャンが正しく表示されることを確認

#### サイズ変更テスト
- [ ] `vehicle.py`でサイズを一時的に変更
- [ ] シミュレーターで大きさの変化を確認
- [ ] 物理挙動（衝突判定）も変化していることを確認
- [ ] 元のサイズに戻す

### 完了確認

- [ ] すべてのテストが成功
- [ ] 手動確認で問題なし
- [ ] コードレビュー（自己レビュー）
  - [ ] ハードコードされた値が削除されている
  - [ ] 型ヒントが正しい
  - [ ] docstringが更新されている
- [ ] 変更をコミット
  ```bash
  git add src/env/renderer.py src/env/minicar_env.py
  git commit -m "Refactor: Eliminate vehicle size duplication

  - Change Renderer.draw_vehicle() to accept Vehicle object
  - Remove hardcoded vehicle dimensions from renderer.py
  - Vehicle size now defined in one place (vehicle.py)
  - Update draw_vehicle() call in minicar_env.py

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## 実装後の確認事項

### コードの品質

- [ ] **DRY原則の達成**: 車両サイズが1箇所のみで定義されている
- [ ] **カプセル化の改善**: 車両の情報は車両オブジェクトから取得
- [ ] **型安全性**: 型ヒントが正しく設定されている
- [ ] **ドキュメント**: docstringが更新されている

### 機能の確認

- [ ] **描画の正確性**: 車両が正しく表示される
- [ ] **物理との一致**: 描画サイズと物理サイズが一致している
- [ ] **パフォーマンス**: レンダリング速度に影響がない

### 保守性の向上

- [ ] **サイズ変更の容易性**: `vehicle.py`の1箇所を変更するだけでよい
- [ ] **拡張性**: 将来的に異なるサイズの車両を扱いやすい

---

## 補足: 将来の拡張案

### 拡張1: 複数の車両タイプのサポート

```python
# vehicle.py
class Vehicle:
    # クラス定数として定義
    VEHICLE_TYPES = {
        "mini": {"length": 0.3, "width": 0.15, "mass": 0.8},
        "standard": {"length": 0.4, "width": 0.2, "mass": 1.0},  # 現在の値
        "large": {"length": 0.5, "width": 0.25, "mass": 1.2},
    }

    def __init__(self, world: b2World, start_pos: Tuple[float, float],
                 start_angle: float = 0.0, vehicle_type: str = "standard"):
        params = self.VEHICLE_TYPES[vehicle_type]
        self.width = params["width"]
        self.length = params["length"]
        self.mass = params["mass"]
        # ...
```

### 拡張2: 車両の色のサポート

```python
# vehicle.py
class Vehicle:
    def __init__(self, ..., color: Tuple[int, int, int] = (0, 150, 255)):
        self.color = color
        # ...

# renderer.py
def draw_vehicle(self, vehicle: "Vehicle"):
    # ...
    pygame.draw.polygon(self.screen, vehicle.color, screen_corners)
```

---

## まとめ

### 変更の要約

| ファイル | 変更内容 | 行数 |
|---------|---------|------|
| `renderer.py` | `draw_vehicle`のシグネチャ変更と実装修正 | +7, -3 |
| `minicar_env.py` | `draw_vehicle`の呼び出し修正 | +1, -1 |
| **合計** | | **+8, -4** |

### 期待される効果

- ✅ **DRY原則の実践**: 重複コードが0箇所に
- ✅ **保守性向上**: サイズ変更が1箇所で完結
- ✅ **バグ防止**: 物理と描画のサイズ不一致を防止
- ✅ **拡張性向上**: 将来的な拡張が容易

### 次のアクション

1. **このプランに従って実装を開始**
2. **各ステップでチェックリストを確認**
3. **完了後、LiDARスキャン最適化に進む**

---

**準備完了！実装を開始してください。**
