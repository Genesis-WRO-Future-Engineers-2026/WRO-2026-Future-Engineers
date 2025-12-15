# 実装開始ガイド

## 1. 開発環境のセットアップ

### 1.1 前提条件

- Python 3.8以上（3.9推奨）
- Git
- （オプション）CUDA対応GPU（学習の高速化）

### 1.2 初期セットアップ手順

#### Step 1: リポジトリのクローン
```bash
cd /Users/akamite/Documents/ichis/minicar-battle/reinforcement-learning/2d-simulator
git status  # 既に初期化済みを確認
```

#### Step 2: 仮想環境の作成
```bash
# venvを使用
python3 -m venv venv
source venv/bin/activate  # Linux/macOS

# または conda
conda create -n minicar-rl python=3.9
conda activate minicar-rl
```

#### Step 3: 依存パッケージのインストール
```bash
# requirements.txtを作成後
pip install -r requirements.txt

# または段階的にインストール
pip install numpy scipy
pip install pybox2d
pip install torch torchvision
pip install gymnasium
pip install pygame matplotlib
pip install tensorboard
pip install pyyaml
pip install pytest black flake8
```

#### Step 4: ディレクトリ構造の作成
```bash
# スクリプトで一括作成
mkdir -p src/{env,physics,rl,curriculum,domain_randomization,utils,deploy}
mkdir -p courses/{easy,medium,hard}
mkdir -p configs
mkdir -p scripts
mkdir -p tests
mkdir -p notebooks
mkdir -p models/{checkpoints,best}
mkdir -p logs/{tensorboard,training}
mkdir -p doc/{design,api}

# __init__.pyファイルの作成
touch src/__init__.py
touch src/env/__init__.py
touch src/physics/__init__.py
touch src/rl/__init__.py
touch src/curriculum/__init__.py
touch src/domain_randomization/__init__.py
touch src/utils/__init__.py
touch src/deploy/__init__.py
```

#### Step 5: .gitignoreの作成
```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Logs and databases
*.log
*.sqlite
logs/
*.db

# Models
models/checkpoints/*.pth
models/checkpoints/*.pt

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# OS
.DS_Store
Thumbs.db

# TensorBoard
events.out.tfevents.*

# Temporary files
tmp/
temp/
*.tmp
EOF
```

#### Step 6: requirements.txtの作成
```bash
cat > requirements.txt << 'EOF'
# Core
numpy==1.24.0
scipy==1.10.0

# Physics
pybox2d==2.3.10

# RL Framework
torch==2.0.0
torchvision==0.15.0
gymnasium==0.29.0

# Visualization
pygame==2.5.0
matplotlib==3.7.0

# Logging
tensorboard==2.13.0

# Config
pyyaml==6.0

# Testing
pytest==7.3.0
pytest-cov==4.1.0

# Code Quality
black==23.3.0
flake8==6.0.0

# Deployment
onnxruntime==1.15.0
EOF
```

#### Step 7: setup.pyの作成（オプション）
```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="minicar-2d-simulator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "pybox2d>=2.3.10",
        "torch>=2.0.0",
        "gymnasium>=0.29.0",
        "pygame>=2.5.0",
        "matplotlib>=3.7.0",
        "tensorboard>=2.13.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
)
```

---

## 2. Phase 1の実装順序

### Week 1: Day 1-2

#### タスク1: Box2Dの動作確認
```python
# tests/test_box2d_basic.py
from Box2D import b2World, b2Vec2

def test_box2d_installation():
    """Box2Dが正しくインストールされているか確認"""
    world = b2World(gravity=(0, 0), doSleep=True)
    assert world is not None

def test_create_body():
    """簡単なボディを作成"""
    world = b2World(gravity=(0, 0))
    body = world.CreateDynamicBody(position=(0, 0))
    body.CreateCircleFixture(radius=1, density=1)

    # シミュレーション
    for _ in range(60):
        world.Step(1/60, 6, 2)

    assert body is not None
```

実行:
```bash
pytest tests/test_box2d_basic.py -v
```

#### タスク2: PhysicsWorldの実装
```python
# src/physics/box2d_wrapper.py
from Box2D import b2World, b2Vec2, b2Body, b2PolygonShape
from typing import List, Tuple

class PhysicsWorld:
    def __init__(self, gravity: Tuple[float, float] = (0, 0)):
        self.world = b2World(gravity=b2Vec2(*gravity), doSleep=True)
        self.time_step = 1.0 / 60.0
        self.vel_iters = 8
        self.pos_iters = 3

    def step(self):
        """物理シミュレーションを1ステップ進める"""
        self.world.Step(self.time_step, self.vel_iters, self.pos_iters)

    def add_static_box(self, center: Tuple[float, float],
                       width: float, height: float) -> b2Body:
        """静的な矩形を追加"""
        body = self.world.CreateStaticBody(
            position=b2Vec2(*center),
            shapes=b2PolygonShape(box=(width/2, height/2))
        )
        return body
```

テスト:
```python
# tests/test_physics_world.py
from src.physics.box2d_wrapper import PhysicsWorld

def test_physics_world_creation():
    world = PhysicsWorld()
    assert world is not None

def test_add_static_box():
    world = PhysicsWorld()
    box = world.add_static_box((5, 5), 1, 1)
    assert box is not None
    assert box.position.x == 5
    assert box.position.y == 5
```

### Week 1: Day 3-4

#### タスク3: Vehicleの基本実装
```python
# src/env/vehicle.py
from Box2D import b2World, b2Vec2, b2Body, b2PolygonShape
import numpy as np
from typing import Tuple, Dict

class Vehicle:
    def __init__(self, world: b2World,
                 start_pos: Tuple[float, float],
                 start_angle: float):
        self.world = world

        # パラメータ
        self.width = 0.2   # m
        self.length = 0.4  # m
        self.mass = 1.0    # kg

        self.max_steering_angle = 0.5  # rad
        self.max_motor_force = 20.0    # N

        # ボディ作成
        self.body = self.world.CreateDynamicBody(
            position=b2Vec2(*start_pos),
            angle=start_angle,
            linearDamping=0.5,
            angularDamping=0.8,
        )

        # 形状
        self.body.CreatePolygonFixture(
            box=(self.length/2, self.width/2),
            density=self.mass / (self.length * self.width),
            friction=0.7,
        )

    def apply_control(self, steering: float, throttle: float):
        """
        制御入力を適用

        Args:
            steering: -1.0 ~ 1.0
            throttle: 0.0 ~ 1.0
        """
        # ステアリング角度
        steer_angle = steering * self.max_steering_angle

        # 車両の向き
        angle = self.body.angle
        direction = b2Vec2(np.cos(angle + steer_angle),
                          np.sin(angle + steer_angle))

        # モーター力を適用
        force = throttle * self.max_motor_force * direction
        self.body.ApplyForceToCenter(force, True)

        # 横滑り抑制（簡易）
        self._apply_lateral_friction()

    def _apply_lateral_friction(self):
        """横方向の速度を抑制"""
        velocity = self.body.linearVelocity
        angle = self.body.angle

        # 車両座標系での速度
        forward = b2Vec2(np.cos(angle), np.sin(angle))
        lateral = b2Vec2(-np.sin(angle), np.cos(angle))

        lateral_vel = velocity.dot(lateral)

        # 横方向の速度を減衰
        impulse = -lateral_vel * self.mass * 0.5 * lateral
        self.body.ApplyLinearImpulse(impulse, self.body.position, True)

    def get_state(self) -> Dict:
        """現在の状態を取得"""
        return {
            'position': (self.body.position.x, self.body.position.y),
            'angle': self.body.angle,
            'velocity': (self.body.linearVelocity.x, self.body.linearVelocity.y),
            'angular_velocity': self.body.angularVelocity,
        }
```

テスト:
```python
# tests/test_vehicle.py
from src.physics.box2d_wrapper import PhysicsWorld
from src.env.vehicle import Vehicle

def test_vehicle_creation():
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)
    assert vehicle is not None

def test_vehicle_forward_motion():
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 前進
    for _ in range(100):
        vehicle.apply_control(steering=0.0, throttle=1.0)
        world.step()

    state = vehicle.get_state()
    # 前方（x正方向）に移動したか
    assert state['position'][0] > 1.0

def test_vehicle_turning():
    world = PhysicsWorld()
    vehicle = Vehicle(world.world, (0, 0), 0)

    # 右旋回
    for _ in range(100):
        vehicle.apply_control(steering=1.0, throttle=0.5)
        world.step()

    state = vehicle.get_state()
    # 角度が変化したか
    assert abs(state['angle']) > 0.1
```

### Week 1: Day 5

#### タスク4: 簡単なコース作成
```json
// courses/easy/simple_oval.json
{
  "name": "Simple Oval",
  "description": "シンプルな楕円コース",
  "start_position": [2.0, 5.0],
  "start_angle": 0.0,
  "goal_position": [2.0, 5.0],
  "goal_radius": 0.5,
  "walls": [
    {
      "type": "polygon",
      "vertices": [
        [0, 0], [10, 0], [10, 10], [0, 10]
      ]
    },
    {
      "type": "polygon",
      "vertices": [
        [2, 2], [8, 2], [8, 8], [2, 8]
      ]
    }
  ]
}
```

#### タスク5: Courseクラスの実装
```python
# src/env/course.py
import json
from typing import List, Tuple, Dict
from Box2D import b2World, b2Vec2, b2PolygonShape
import numpy as np

class Course:
    def __init__(self, course_file: str):
        with open(course_file, 'r') as f:
            self.data = json.load(f)

        self.walls = []

    def create_walls(self, world: b2World):
        """Box2Dの静的bodyとして壁を生成"""
        for wall_data in self.data['walls']:
            vertices = wall_data['vertices']

            # 閉じたポリゴンとして各辺を作成
            for i in range(len(vertices)):
                v1 = vertices[i]
                v2 = vertices[(i + 1) % len(vertices)]

                # 線分として壁を作成
                self._create_wall_segment(world, v1, v2)

    def _create_wall_segment(self, world: b2World,
                            v1: List[float], v2: List[float]):
        """2点間に壁を作成"""
        # 中点
        center = [(v1[0] + v2[0]) / 2, (v1[1] + v2[1]) / 2]

        # 長さと角度
        dx = v2[0] - v1[0]
        dy = v2[1] - v1[1]
        length = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)

        # 静的ボディ作成
        body = world.CreateStaticBody(
            position=b2Vec2(*center),
            angle=angle,
            shapes=b2PolygonShape(box=(length/2, 0.05))  # 薄い矩形
        )
        self.walls.append(body)

    def get_start_pose(self) -> Tuple[Tuple[float, float], float]:
        """スタート位置と角度"""
        pos = tuple(self.data['start_position'])
        angle = self.data['start_angle']
        return pos, angle
```

---

## 3. 開発ワークフロー

### 3.1 日々の開発サイクル

1. **朝**: タスクの確認、目標設定
2. **午前**: 実装 + ユニットテスト
3. **午後**: 統合テスト + デバッグ
4. **夕方**: コードレビュー、コミット

### 3.2 テスト駆動開発

```bash
# 開発サイクル
# 1. テストを書く
vim tests/test_vehicle.py

# 2. テストが失敗することを確認
pytest tests/test_vehicle.py

# 3. 実装
vim src/env/vehicle.py

# 4. テストがパスすることを確認
pytest tests/test_vehicle.py

# 5. リファクタリング
# 6. 再度テスト
```

### 3.3 コードフォーマット

```bash
# コードフォーマット
black src/ tests/

# リンター
flake8 src/ tests/

# 型チェック（オプション）
mypy src/
```

---

## 4. デバッグのヒント

### 4.1 Pygameデバッグ表示

```python
# 車両の状態をデバッグ表示
def render_debug_info(screen, vehicle):
    import pygame
    font = pygame.font.Font(None, 24)

    state = vehicle.get_state()
    texts = [
        f"Pos: ({state['position'][0]:.2f}, {state['position'][1]:.2f})",
        f"Angle: {state['angle']:.2f}",
        f"Vel: {np.linalg.norm(state['velocity']):.2f}",
    ]

    y_offset = 10
    for text in texts:
        surface = font.render(text, True, (255, 255, 255))
        screen.blit(surface, (10, y_offset))
        y_offset += 30
```

### 4.2 ログ出力

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Vehicle position: %s", vehicle.get_state()['position'])
```

---

## 5. 次のステップ

Phase 1のタスクを完了したら:

1. **動作確認**: 手動制御で走行テスト
2. **デモ動画**: 録画して記録
3. **レビュー**: コードレビュー実施
4. **Phase 2へ**: PPO実装に進む

---

## まとめ

このガイドに従って段階的に実装を進めることで、着実にプロジェクトを進めることができます。特にテスト駆動開発を意識し、各コンポーネントが独立して動作することを確認しながら進めてください。
