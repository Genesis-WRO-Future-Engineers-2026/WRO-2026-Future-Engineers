# Box2D衝突検出による壁衝突判定の修正計画

## 実装日時
2025-12-11

## 問題の概要

### 現状の問題
壁との衝突判定が甘く、以下の問題が発生している:
1. 斜めにぶつかった時に衝突が検出されない
2. 正面からぶつかった時でも衝突が検出されないケースがある
3. 衝突判定の失敗により、適切に学習エピソードがリセットされない

### 根本原因の特定

#### 1. LiDARベースの衝突判定の限界
**場所**: `src/env/minicar_env.py:262-266`

```python
# 壁衝突（LiDARの最小距離が衝突閾値以下）
min_distance = np.min(lidar_scan)
if min_distance <= self.COLLISION_DISTANCE:
    self.is_collision = True
    return True
```

**問題点**:
- LiDARは前方120度（-60°～+60°）しかカバーしていない（`minicar_env.py:58-64`）
- レイ本数が5本のみで、検出範囲に大きな死角がある
- **側面や後部からの衝突は完全に検出不可能**
- 斜めの衝突時、LiDARのレイが壁を捉えられないケースがある

#### 2. 衝突距離の設定の不適切さ
**場所**: `src/env/minicar_env.py:23`

```python
COLLISION_DISTANCE = 0.22  # 壁衝突とみなす距離（m）
```

**問題点**:
- 車両の対角線半径（約0.224m）を基準にしているが、LiDARは車両中心から発射
- 前方120度のみのカバレッジでは、車両の角や辺が先にぶつかっても検出できない
- LiDARのレイが疎なため、壁との接触前に距離閾値を通過してしまう

#### 3. Box2Dの物理衝突機能が未活用
**Box2Dの衝突検出機能**:
- Box2D物理エンジンは正確な衝突検出機能を標準搭載
- 現在の実装では`b2ContactListener`を一切使用していない
- すべての物理的接触を正確に検出可能（全方向、全角度）

## 解決方針：Box2D ContactListenerの採用

### なぜBox2Dの衝突検出を使うべきか

#### メリット
1. **正確性**: 物理エンジンレベルでの厳密な衝突検出
2. **全方向対応**: 前後左右、どの角度からの衝突も確実に検出
3. **計算効率**: 物理シミュレーション中に自動的に検出されるため、追加コストが極小
4. **保守性**: LiDARは観測空間として維持し、衝突判定は物理エンジンに任せるという責任分離
5. **学習への影響最小**: 観測空間（LiDAR）は変更せず、終了判定のみを改善

#### LiDARとの役割分離
- **LiDAR**: 強化学習の観測空間（前方の障害物距離を知る）
- **Box2D衝突検出**: 終了条件の判定（実際に壁にぶつかったかを知る）

この分離により、エージェントは前方のセンサー情報で学習しつつ、実際の衝突は正確に検出できる。

## 実装計画

### フェーズ1: ContactListenerの実装

#### 1-1. CollisionListenerクラスの作成
**ファイル**: `src/physics/collision_listener.py`（新規作成）

```python
"""Box2D衝突検出リスナー"""

from Box2D import b2ContactListener


class CollisionListener(b2ContactListener):
    """車両と壁の衝突を検出するContactListener"""

    def __init__(self):
        """
        ContactListenerを初期化

        Note:
            - collision_detected: 衝突が検出されたかのフラグ
            - 各ステップ開始時にリセットする必要がある
        """
        b2ContactListener.__init__(self)
        self.collision_detected = False

    def BeginContact(self, contact):
        """
        2つのfixtureが接触を開始した時に呼ばれる

        Args:
            contact: b2Contact オブジェクト

        Note:
            - contact.fixtureA, contact.fixtureBで接触した2つのfixtureを取得
            - fixture.body.userDataで各bodyの識別子を取得
            - 車両("vehicle")と壁("wall")の接触を検出
        """
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB

        body_a = fixture_a.body
        body_b = fixture_b.body

        # userDataで車両と壁を識別
        user_data_a = body_a.userData
        user_data_b = body_b.userData

        # 車両と壁の衝突を検出
        if (user_data_a == "vehicle" and user_data_b == "wall") or \
           (user_data_a == "wall" and user_data_b == "vehicle"):
            self.collision_detected = True

    def EndContact(self, contact):
        """
        2つのfixtureの接触が終了した時に呼ばれる

        Args:
            contact: b2Contact オブジェクト

        Note:
            現在の実装では使用しないが、将来的な拡張のために定義
        """
        pass

    def reset(self):
        """
        衝突フラグをリセット

        Note:
            各ステップまたはエピソード開始時に呼び出す
        """
        self.collision_detected = False

    def is_collision(self) -> bool:
        """
        衝突が検出されたかを返す

        Returns:
            衝突が検出された場合True
        """
        return self.collision_detected
```

**設計のポイント**:
- `BeginContact`で車両と壁の接触を検出
- `userData`を使って車両と壁を識別
- シンプルなフラグベースの実装で、エピソード中の衝突を記録
- `reset()`メソッドで各エピソード開始時にフラグをクリア

### フェーズ2: 既存コードへのuserData追加

#### 2-1. 車両にuserDataを設定
**ファイル**: `src/env/vehicle.py`

**変更箇所**: `Vehicle.__init__`メソッド（69-82行目付近）

**変更前**:
```python
# Box2Dボディ作成
self.body = self.world.CreateDynamicBody(
    position=b2Vec2(*start_pos),
    angle=start_angle,
    linearDamping=0.5,  # 空気抵抗
    angularDamping=0.8,  # 回転抵抗
)

# 車両の形状（矩形）
self.body.CreatePolygonFixture(
    box=(self.length / 2, self.width / 2),
    density=self.mass / (self.length * self.width),
    friction=0.7,
)
```

**変更後**:
```python
# Box2Dボディ作成
self.body = self.world.CreateDynamicBody(
    position=b2Vec2(*start_pos),
    angle=start_angle,
    linearDamping=0.5,  # 空気抵抗
    angularDamping=0.8,  # 回転抵抗
)

# 車両の識別子を設定（衝突検出用）
self.body.userData = "vehicle"

# 車両の形状（矩形）
self.body.CreatePolygonFixture(
    box=(self.length / 2, self.width / 2),
    density=self.mass / (self.length * self.width),
    friction=0.7,
)
```

**追加される行**: `self.body.userData = "vehicle"`（1行追加）

#### 2-2. 壁にuserDataを設定
**ファイル**: `src/env/course.py`

**変更箇所**: `Course._create_wall_segment`メソッド（74-99行目）

**変更前**:
```python
def _create_wall_segment(
    self,
    world: b2World,
    v1: List[float],
    v2: List[float],
    thickness: float = 0.1,
):
    """2点間に壁セグメントを作成"""
    # 中点
    center = [(v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2]

    # 長さと角度
    dx = v2[0] - v1[0]
    dy = v2[1] - v1[1]
    length = np.sqrt(dx**2 + dy**2)
    angle = np.arctan2(dy, dx)

    # 静的ボディ作成
    from Box2D import b2PolygonShape

    body = world.CreateStaticBody(
        position=b2Vec2(*center),
        angle=angle,
        shapes=b2PolygonShape(box=(length / 2, thickness / 2)),
    )
    return body
```

**変更後**:
```python
def _create_wall_segment(
    self,
    world: b2World,
    v1: List[float],
    v2: List[float],
    thickness: float = 0.1,
):
    """2点間に壁セグメントを作成"""
    # 中点
    center = [(v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2]

    # 長さと角度
    dx = v2[0] - v1[0]
    dy = v2[1] - v1[1]
    length = np.sqrt(dx**2 + dy**2)
    angle = np.arctan2(dy, dx)

    # 静的ボディ作成
    from Box2D import b2PolygonShape

    body = world.CreateStaticBody(
        position=b2Vec2(*center),
        angle=angle,
        shapes=b2PolygonShape(box=(length / 2, thickness / 2)),
    )

    # 壁の識別子を設定（衝突検出用）
    body.userData = "wall"

    return body
```

**追加される行**: `body.userData = "wall"`（1行追加）

### フェーズ3: PhysicsWorldへのContactListener統合

#### 3-1. PhysicsWorldクラスの拡張
**ファイル**: `src/physics/box2d_wrapper.py`

**変更箇所1**: importの追加（1-5行目付近）

**変更前**:
```python
"""Box2D物理エンジンのラッパークラス"""

from Box2D import b2World, b2Vec2, b2Body, b2PolygonShape
from typing import List, Tuple
```

**変更後**:
```python
"""Box2D物理エンジンのラッパークラス"""

from Box2D import b2World, b2Vec2, b2Body, b2PolygonShape
from typing import List, Tuple, Optional

from src.physics.collision_listener import CollisionListener
```

**変更箇所2**: `PhysicsWorld.__init__`メソッドの拡張（10-18行目）

**変更前**:
```python
def __init__(self, gravity: Tuple[float, float] = (0, 0)):
    """
    Args:
        gravity: 重力ベクトル (x, y)。2Dレースなので通常は(0, 0)
    """
    self.world = b2World(gravity=b2Vec2(*gravity), doSleep=True)
    self.time_step = 1.0 / 60.0  # 60Hz
    self.vel_iters = 8  # 速度反復回数
    self.pos_iters = 3  # 位置反復回数
```

**変更後**:
```python
def __init__(
    self,
    gravity: Tuple[float, float] = (0, 0),
    collision_listener: Optional[CollisionListener] = None
):
    """
    Args:
        gravity: 重力ベクトル (x, y)。2Dレースなので通常は(0, 0)
        collision_listener: 衝突検出リスナー（オプション）
    """
    self.world = b2World(gravity=b2Vec2(*gravity), doSleep=True)
    self.time_step = 1.0 / 60.0  # 60Hz
    self.vel_iters = 8  # 速度反復回数
    self.pos_iters = 3  # 位置反復回数

    # ContactListenerを登録
    self.collision_listener = collision_listener
    if self.collision_listener is not None:
        self.world.contactListener = self.collision_listener
```

**変更箇所3**: 衝突状態取得メソッドの追加（新規メソッド）

**追加するメソッド**:
```python
def has_collision(self) -> bool:
    """
    衝突が検出されたかを返す

    Returns:
        衝突が検出された場合True、リスナーが未設定の場合False
    """
    if self.collision_listener is not None:
        return self.collision_listener.is_collision()
    return False

def reset_collision(self):
    """
    衝突フラグをリセット

    Note:
        各エピソード開始時に呼び出す
    """
    if self.collision_listener is not None:
        self.collision_listener.reset()
```

**追加位置**: `step()`メソッドの後（22-23行目の後）

### フェーズ4: MinicarEnvへの統合

#### 4-1. MinicarEnv.__init__の変更
**ファイル**: `src/env/minicar_env.py`

**変更箇所1**: importの追加（1-12行目付近）

**変更前**:
```python
"""Gym互換のミニカー環境"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Optional, Any

from src.physics.box2d_wrapper import PhysicsWorld
from src.env.vehicle import Vehicle
from src.env.sensors import LiDARSensor, LIDAR_MAX_RANGE
from src.env.course import Course
from src.env.renderer import Renderer
```

**変更後**:
```python
"""Gym互換のミニカー環境"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Optional, Any

from src.physics.box2d_wrapper import PhysicsWorld
from src.physics.collision_listener import CollisionListener
from src.env.vehicle import Vehicle
from src.env.sensors import LiDARSensor, LIDAR_MAX_RANGE
from src.env.course import Course
from src.env.renderer import Renderer
```

**変更箇所2**: `__init__`メソッドでContactListenerを初期化（27-56行目付近）

**変更前**:
```python
# コースのロード
self.course = Course(course_file)

# 物理世界
self.world = PhysicsWorld()

# 壁の作成
self.course.create_walls(self.world.world)
```

**変更後**:
```python
# コースのロード
self.course = Course(course_file)

# 衝突検出リスナーを作成
self.collision_listener = CollisionListener()

# 物理世界（ContactListenerを登録）
self.world = PhysicsWorld(collision_listener=self.collision_listener)

# 壁の作成
self.course.create_walls(self.world.world)
```

#### 4-2. reset()メソッドの変更
**変更箇所**: `reset()`メソッド（97-128行目）

**変更前**:
```python
def reset(
    self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    環境をリセット

    Returns:
        observation, info
    """
    super().reset(seed=seed)

    # 車両をリセット
    start_pos, start_angle = self.course.get_start_pose()
    self.vehicle.reset(start_pos, start_angle)

    # 状態をリセット
    self.step_count = 0
    self.last_action = np.zeros(2)
    self.total_reward = 0.0
    self.next_checkpoint_index = 0  # 次のチェックポイントをリセット
    self.is_collision = False  # 衝突フラグをリセット
```

**変更後**:
```python
def reset(
    self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    環境をリセット

    Returns:
        observation, info
    """
    super().reset(seed=seed)

    # 車両をリセット
    start_pos, start_angle = self.course.get_start_pose()
    self.vehicle.reset(start_pos, start_angle)

    # 状態をリセット
    self.step_count = 0
    self.last_action = np.zeros(2)
    self.total_reward = 0.0
    self.next_checkpoint_index = 0  # 次のチェックポイントをリセット
    self.is_collision = False  # 衝突フラグをリセット

    # 衝突検出リスナーをリセット
    self.world.reset_collision()
```

**追加される行**: `self.world.reset_collision()`（1行追加）

#### 4-3. _check_terminated()メソッドの変更
**変更箇所**: `_check_terminated()`メソッド（245-268行目）

**変更前**:
```python
def _check_terminated(self) -> bool:
    """
    終了条件をチェック

    Returns:
        終了したかどうか
    """
    # キャッシュされたデータを使用
    state = self._cached_vehicle_state
    lidar_scan = self._cached_lidar_scan

    # ゴール到達（すべてのチェックポイントを順番に通過している必要がある）
    checkpoints = self.course.get_checkpoints()
    all_checkpoints_passed = self.next_checkpoint_index == len(checkpoints)
    if all_checkpoints_passed and self.course.check_goal(state["position"]):
        return True

    # 壁衝突（LiDARの最小距離が衝突閾値以下）
    min_distance = np.min(lidar_scan)
    if min_distance <= self.COLLISION_DISTANCE:
        self.is_collision = True  # 衝突フラグを立てる
        return True

    return False
```

**変更後**:
```python
def _check_terminated(self) -> bool:
    """
    終了条件をチェック

    Returns:
        終了したかどうか
    """
    # キャッシュされたデータを使用
    state = self._cached_vehicle_state

    # ゴール到達（すべてのチェックポイントを順番に通過している必要がある）
    checkpoints = self.course.get_checkpoints()
    all_checkpoints_passed = self.next_checkpoint_index == len(checkpoints)
    if all_checkpoints_passed and self.course.check_goal(state["position"]):
        return True

    # 壁衝突（Box2Dの物理衝突検出を使用）
    if self.world.has_collision():
        self.is_collision = True  # 衝突フラグを立てる
        return True

    return False
```

**変更点**:
- LiDARベースの衝突判定を削除
- Box2Dの`has_collision()`を使用した物理ベースの衝突判定に置き換え
- `lidar_scan`変数は不要になったため削除

**注意**: `_compute_reward()`メソッドではLiDARベースの壁接近ペナルティを**維持**する。これは報酬設計の一部であり、衝突判定とは別の目的。

#### 4-4. load_course()メソッドの変更
**変更箇所**: `load_course()`メソッド（366-408行目）

**変更前**:
```python
# 物理世界をリセット
self.world = PhysicsWorld()

# 新しいコースをロード
self.course = Course(course_file)
```

**変更後**:
```python
# 衝突検出リスナーをリセット
self.collision_listener.reset()

# 物理世界をリセット（同じリスナーを再利用）
self.world = PhysicsWorld(collision_listener=self.collision_listener)

# 新しいコースをロード
self.course = Course(course_file)
```

**追加される行**: `self.collision_listener.reset()`とContactListenerの引数追加

### フェーズ5: 定数の削除または非推奨化

#### 5-1. COLLISION_DISTANCEの扱い
**ファイル**: `src/env/minicar_env.py`

**変更箇所**: クラス定数（20-25行目）

**変更前**:
```python
# 衝突判定パラメータ
# 車両の対角線半径は約0.224m（幅0.2m × 長さ0.4m）
# LiDARは車両中心から発射されるため、壁接触時のmin_distanceは約0.22mになる
COLLISION_DISTANCE = 0.22  # 壁衝突とみなす距離（m）
WALL_APPROACH_DISTANCE = 0.3  # 壁接近ペナルティの閾値（m）
COLLISION_PENALTY = -100.0  # 衝突時の報酬ペナルティ
```

**変更後**:
```python
# 衝突判定パラメータ
# NOTE: 衝突判定はBox2Dの物理エンジンで行うため、COLLISION_DISTANCEは使用しない
# WALL_APPROACH_DISTANCEは報酬設計で壁接近ペナルティを与えるために使用
WALL_APPROACH_DISTANCE = 0.3  # 壁接近ペナルティの閾値（m）
COLLISION_PENALTY = -100.0  # 衝突時の報酬ペナルティ
```

**変更点**:
- `COLLISION_DISTANCE`を削除
- コメントを更新して、Box2D物理エンジンによる衝突検出を明記
- `WALL_APPROACH_DISTANCE`と`COLLISION_PENALTY`は報酬設計で引き続き使用

## テスト計画

### 1. 単体テスト

#### 1-1. CollisionListenerのテスト
**ファイル**: `tests/test_collision_listener.py`（新規作成）

```python
"""CollisionListenerの単体テスト"""

import pytest
from Box2D import b2World, b2Vec2
from src.physics.collision_listener import CollisionListener


def test_collision_listener_initialization():
    """CollisionListenerの初期化テスト"""
    listener = CollisionListener()
    assert listener.is_collision() == False


def test_collision_listener_reset():
    """CollisionListenerのリセットテスト"""
    listener = CollisionListener()
    listener.collision_detected = True
    assert listener.is_collision() == True

    listener.reset()
    assert listener.is_collision() == False


def test_vehicle_wall_collision_detection():
    """車両と壁の衝突検出テスト"""
    # Box2D世界を作成
    listener = CollisionListener()
    world = b2World(gravity=(0, 0), doSleep=True)
    world.contactListener = listener

    # 車両ボディを作成
    vehicle_body = world.CreateDynamicBody(
        position=(0, 0)
    )
    vehicle_body.userData = "vehicle"
    vehicle_body.CreatePolygonFixture(box=(0.2, 0.1), density=1.0)

    # 壁ボディを作成（車両のすぐ近く）
    wall_body = world.CreateStaticBody(
        position=(0.5, 0)
    )
    wall_body.userData = "wall"
    wall_body.CreatePolygonFixture(box=(0.1, 1.0))

    # 衝突前は検出されていない
    assert listener.is_collision() == False

    # 車両を壁に向かって移動
    vehicle_body.linearVelocity = b2Vec2(10, 0)

    # 物理シミュレーションを進める
    for _ in range(100):
        world.Step(1.0/60.0, 8, 3)
        if listener.is_collision():
            break

    # 衝突が検出されたことを確認
    assert listener.is_collision() == True
```

#### 1-2. PhysicsWorldの統合テスト
**ファイル**: `tests/test_physics_world_collision.py`（新規作成）

```python
"""PhysicsWorldのCollisionListener統合テスト"""

import pytest
from Box2D import b2Vec2
from src.physics.box2d_wrapper import PhysicsWorld
from src.physics.collision_listener import CollisionListener


def test_physics_world_with_collision_listener():
    """PhysicsWorldにCollisionListenerを統合したテスト"""
    listener = CollisionListener()
    world = PhysicsWorld(collision_listener=listener)

    # 衝突リスナーが正しく登録されているか
    assert world.collision_listener == listener
    assert world.world.contactListener == listener


def test_physics_world_collision_detection():
    """PhysicsWorldでの衝突検出テスト"""
    listener = CollisionListener()
    world = PhysicsWorld(collision_listener=listener)

    # 車両を作成
    vehicle_body = world.world.CreateDynamicBody(position=(0, 0))
    vehicle_body.userData = "vehicle"
    vehicle_body.CreatePolygonFixture(box=(0.2, 0.1), density=1.0)

    # 壁を作成
    wall_body = world.world.CreateStaticBody(position=(0.5, 0))
    wall_body.userData = "wall"
    wall_body.CreatePolygonFixture(box=(0.1, 1.0))

    # 初期状態
    assert world.has_collision() == False

    # 車両を壁に向かって移動
    vehicle_body.linearVelocity = b2Vec2(10, 0)

    # 衝突するまでシミュレーション
    for _ in range(100):
        world.step()
        if world.has_collision():
            break

    # 衝突が検出されたことを確認
    assert world.has_collision() == True

    # リセット
    world.reset_collision()
    assert world.has_collision() == False
```

### 2. 統合テスト

#### 2-1. MinicarEnvの衝突検出テスト
**ファイル**: `tests/test_env_collision.py`（既存ファイルに追加）

```python
"""MinicarEnvの衝突検出統合テスト"""

import pytest
import numpy as np
from src.env.minicar_env import MinicarEnv


def test_env_box2d_collision_detection():
    """環境でBox2D衝突検出が機能するかテスト"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, info = env.reset()

    # 初期状態では衝突なし
    assert env.world.has_collision() == False
    assert env.is_collision == False

    # 壁に向かって全速前進（衝突するまで）
    for _ in range(500):
        action = np.array([0.0, 1.0])  # まっすぐ前進
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated:
            # 衝突で終了したことを確認
            assert env.is_collision == True
            assert info["is_collision"] == True
            break

    # 衝突で終了したことを確認
    assert terminated == True
    assert env.is_collision == True


def test_env_side_collision():
    """側面衝突が検出されるかテスト"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")
    obs, info = env.reset()

    # 横向きに移動させるために、ステアリングと前進を組み合わせる
    collision_detected = False

    for _ in range(1000):
        # 右に旋回しながら前進（壁に横から衝突する可能性を高める）
        action = np.array([1.0, 1.0])
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated and env.is_collision:
            collision_detected = True
            break

    # 最終的に衝突が検出されることを確認
    # （側面衝突も検出可能になったことの確認）
    assert collision_detected == True


def test_env_collision_reset():
    """衝突フラグがリセットで正しくクリアされるかテスト"""
    env = MinicarEnv(course_file="courses/easy/simple_oval.json")

    # 1回目のエピソード：衝突させる
    obs, info = env.reset()
    for _ in range(500):
        action = np.array([0.0, 1.0])
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated:
            break

    # 衝突フラグが立っている
    assert env.is_collision == True

    # リセット
    obs, info = env.reset()

    # フラグがクリアされている
    assert env.is_collision == False
    assert env.world.has_collision() == False
```

### 3. 手動テスト（GUI）

#### 3-1. 視覚的な衝突検出の確認
**目的**: GUIで実際に車両を操作して、あらゆる角度からの衝突が検出されることを確認

**手順**:
1. `python scripts/simulator-demo/manual_control.py`を実行
2. 以下のシナリオを手動で実行:
   - 正面衝突
   - 斜め45度からの衝突
   - 側面衝突（左右）
   - 後退中の衝突
   - 高速での衝突
   - 低速での衝突

**期待結果**: すべてのケースで衝突が検出され、即座にエピソードが終了する

#### 3-2. 学習中の動作確認
**目的**: 学習中に衝突検出が正しく機能し、適切にエピソードがリセットされることを確認

**手順**:
1. `python scripts/rl-training/train.py --total-iterations 10 --gui`を実行
2. 学習初期段階（ランダム行動が多い時期）での衝突を観察
3. コンソール出力で`is_collision: True`が適切に出ているか確認

**期待結果**:
- 壁にぶつかったら即座にエピソード終了
- リセット後、衝突フラグがクリアされている
- 学習が正常に進行する

## 実装の注意点

### 1. Box2Dの制約
**重要**: ContactListenerのコールバック内でBox2Dエンティティの作成・削除は禁止

```python
# ❌ NG: コールバック内でbodyを作成・削除
def BeginContact(self, contact):
    self.world.DestroyBody(body)  # 禁止！

# ✅ OK: フラグを立てるだけ
def BeginContact(self, contact):
    self.collision_detected = True  # これはOK
```

### 2. ContactListenerの寿命管理
- ContactListenerは`b2World`オブジェクトが存在する間、スコープ内に存在する必要がある
- `MinicarEnv`のメンバー変数として保持することで、ガベージコレクションを回避

### 3. 後方互換性
- 既存の保存済みモデルは引き続き使用可能
- 観測空間（LiDAR）は変更していないため、ポリシーネットワークに影響なし
- 学習アルゴリズムの変更なし

### 4. パフォーマンス
- Box2Dの衝突検出は物理シミュレーション中に自動実行されるため、追加コストはほぼゼロ
- LiDARベースの判定よりも計算効率が良い（最小距離計算が不要）

## デグレードのリスクと対策

### リスク1: 衝突判定が厳しすぎる
**現象**: わずかな接触でも衝突と判定され、学習が進まない

**対策**:
- センサー（軽微な接触を無視）の導入を検討
- 接触の強さ（インパルス）を閾値判定に使用

**コード例** (必要に応じて実装):
```python
def BeginContact(self, contact):
    # インパルスの大きさで判定（PreSolve/PostSolveで取得可能）
    # 軽微な接触は無視する場合に使用
    pass
```

### リスク2: 学習済みモデルの性能低下
**現象**: 衝突判定が正確になったことで、これまで誤って通過していたケースが検出され、成功率が下がる

**対策**:
- これは正常な動作（正しい衝突検出による適切な評価）
- 必要に応じて再学習を実施
- カリキュラム学習で段階的に難易度を調整

## 実装スケジュール

### Day 1: 基礎実装
- [ ] フェーズ1: `CollisionListener`クラスの実装
- [ ] フェーズ2: `userData`の追加（Vehicle, Course）
- [ ] フェーズ3: `PhysicsWorld`への統合

### Day 2: 環境統合とテスト
- [ ] フェーズ4: `MinicarEnv`への統合
- [ ] フェーズ5: 定数の整理
- [ ] 単体テストの作成と実行

### Day 3: 検証と調整
- [ ] 統合テストの実行
- [ ] GUIでの手動テスト
- [ ] 学習動作の確認
- [ ] ドキュメント更新

## 成功基準

### 定量的指標
1. **全方向衝突検出率**: 100%（前後左右、すべての角度）
2. **誤検出率**: 0%（衝突していないのに検出される）
3. **テストカバレッジ**: 90%以上（新規コード）
4. **パフォーマンス**: FPS低下 < 5%

### 定性的指標
1. 手動操作で、あらゆる角度からの衝突が即座に検出される
2. 学習が正常に進行し、エピソードが適切にリセットされる
3. コードの可読性と保守性が向上している

## まとめ

この実装計画により、以下を達成する:

1. **正確な衝突検出**: Box2Dの物理エンジンによる全方向・全角度の確実な検出
2. **責任分離**: LiDAR（観測）と衝突検出（終了判定）の明確な分離
3. **保守性向上**: 物理エンジンの機能を活用し、手動実装の削減
4. **後方互換性**: 観測空間を変更せず、既存モデルへの影響を最小化
5. **学習品質向上**: 正確な終了判定による適切な学習フィードバック

この計画に従って実装することで、壁衝突判定の問題を根本的に解決できる。
