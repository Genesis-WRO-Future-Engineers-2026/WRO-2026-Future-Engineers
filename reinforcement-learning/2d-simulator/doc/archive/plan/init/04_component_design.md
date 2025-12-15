# コンポーネント詳細設計

## 1. シミュレーション環境 (`src/env/`)

### 1.1 MinicarEnv (minicar_env.py)

Gym互換の環境クラス。すべてのコンポーネントを統合。

#### クラス定義
```python
class MinicarEnv(gym.Env):
    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': 30}

    def __init__(self, config: dict):
        """
        Args:
            config: 環境設定（YAMLから読み込み）
        """

    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, dict]:
        """環境をリセット"""

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        Args:
            action: [steering, throttle] (-1~1, 0~1)
        Returns:
            observation, reward, terminated, truncated, info
        """

    def render(self):
        """Pygameで描画"""

    def close(self):
        """リソースの解放"""
```

#### 観測空間
```python
observation_space = gym.spaces.Dict({
    'lidar': gym.spaces.Box(low=0, high=10, shape=(72,), dtype=np.float32),
    'velocity': gym.spaces.Box(low=-10, high=10, shape=(2,), dtype=np.float32),
    'angular_velocity': gym.spaces.Box(low=-5, high=5, shape=(1,), dtype=np.float32),
    'last_action': gym.spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32),
})
```

**フラット化した観測（PPO用）:**
```python
# 合計77次元
obs_flat = np.concatenate([
    lidar_scan,           # 72
    velocity,             # 2 (vx, vy)
    angular_velocity,     # 1
    last_action,          # 2 (steering, throttle)
])
```

#### 行動空間
```python
action_space = gym.spaces.Box(
    low=np.array([-1.0, 0.0]),   # [min_steering, min_throttle]
    high=np.array([1.0, 1.0]),   # [max_steering, max_throttle]
    dtype=np.float32
)
```

#### 報酬関数
```python
def _compute_reward(self) -> float:
    reward = 0.0

    # 1. 前進報酬（コース進行）
    progress = self._get_course_progress()
    reward += progress * 1.0

    # 2. 速度報酬
    speed = np.linalg.norm(self.vehicle.velocity)
    reward += speed * 0.1

    # 3. 時間ペナルティ
    reward -= 0.01

    # 4. 壁接近ペナルティ
    min_distance = np.min(self.lidar_scan)
    if min_distance < 0.3:
        reward -= (0.3 - min_distance) * 10

    # 5. 壁衝突（終了）
    if self._check_collision():
        reward -= 100

    # 6. ゴール到達
    if self._check_goal():
        reward += 500

    return reward
```

---

### 1.2 Vehicle (vehicle.py)

車両の物理モデルと制御。

#### クラス定義
```python
class Vehicle:
    def __init__(self, world: b2World, start_pos: Tuple[float, float], start_angle: float):
        self.body = None  # Box2Dのbody
        self.width = 0.2  # m
        self.length = 0.4  # m
        self.mass = 1.0   # kg

        self.max_steering_angle = 0.5  # rad
        self.max_motor_force = 20.0    # N

    def apply_control(self, steering: float, throttle: float):
        """制御入力を適用"""

    def get_state(self) -> dict:
        """現在の状態を取得"""
        return {
            'position': self.body.position,
            'angle': self.body.angle,
            'velocity': self.body.linearVelocity,
            'angular_velocity': self.body.angularVelocity,
        }
```

#### 制御モデル（Ackermann steering）
```python
def apply_control(self, steering: float, throttle: float):
    # ステアリング角度
    steer_angle = steering * self.max_steering_angle

    # 前後の車輪位置
    rear_wheel_pos = self.body.position
    front_wheel_pos = rear_wheel_pos + self.length * Vec2(cos(angle), sin(angle))

    # モーター力
    motor_force = throttle * self.max_motor_force
    force_direction = Vec2(cos(angle + steer_angle), sin(angle + steer_angle))
    self.body.ApplyForce(motor_force * force_direction, front_wheel_pos, True)

    # 横滑り抑制（簡易的な摩擦モデル）
    lateral_velocity = self._get_lateral_velocity()
    impulse = -lateral_velocity * self.mass * 0.5
    self.body.ApplyLinearImpulse(impulse, self.body.position, True)
```

---

### 1.3 LiDAR Sensor (sensors.py)

レイキャスティングによる距離測定。

#### クラス定義
```python
class LiDARSensor:
    def __init__(self, world: b2World, num_rays: int = 72, max_range: float = 10.0):
        self.world = world
        self.num_rays = num_rays
        self.max_range = max_range
        self.angle_increment = 2 * np.pi / num_rays

    def scan(self, position: Vec2, orientation: float) -> np.ndarray:
        """
        Returns:
            distances: (num_rays,) 各方向の距離
        """
        distances = np.zeros(self.num_rays)

        for i in range(self.num_rays):
            angle = orientation + i * self.angle_increment
            direction = Vec2(np.cos(angle), np.sin(angle))

            # レイキャスト
            hit_point, hit_distance = self._raycast(position, direction)
            distances[i] = hit_distance if hit_distance else self.max_range

        return distances

    def _raycast(self, start: Vec2, direction: Vec2) -> Tuple[Vec2, float]:
        """Box2Dのレイキャスト"""
        # RayCastCallback実装
        ...
```

#### ノイズモデル
```python
def add_noise(self, distances: np.ndarray, noise_level: float = 0.01) -> np.ndarray:
    """
    ガウシアンノイズを追加
    """
    noise = np.random.normal(0, noise_level * self.max_range, distances.shape)
    return np.clip(distances + noise, 0, self.max_range)
```

---

### 1.4 Course (course.py)

コースの定義とロード。

#### JSON形式
```json
{
  "name": "simple_oval",
  "start_position": [1.0, 1.0],
  "start_angle": 0.0,
  "goal_position": [1.0, 1.0],
  "goal_radius": 0.5,
  "walls": [
    {
      "type": "polygon",
      "vertices": [[0, 0], [10, 0], [10, 8], [0, 8]]
    }
  ],
  "checkpoints": [
    {"position": [5.0, 1.0], "radius": 1.0},
    {"position": [9.0, 4.0], "radius": 1.0}
  ]
}
```

#### クラス定義
```python
class Course:
    def __init__(self, course_file: str):
        self.data = self._load_json(course_file)
        self.walls = []

    def create_walls(self, world: b2World):
        """Box2Dの静的bodyとして壁を生成"""
        for wall_data in self.data['walls']:
            vertices = wall_data['vertices']
            # staticBodyとしてポリゴン生成
            ...

    def get_start_pose(self) -> Tuple[Vec2, float]:
        """スタート位置と角度"""

    def check_checkpoint(self, position: Vec2) -> int:
        """チェックポイント通過判定"""
```

---

## 2. 物理エンジン (`src/physics/`)

### 2.1 Box2D Wrapper (box2d_wrapper.py)

Box2Dの初期化と管理。

```python
class PhysicsWorld:
    def __init__(self, gravity: Vec2 = (0, 0)):
        self.world = b2World(gravity=gravity, doSleep=True)
        self.time_step = 1.0 / 60.0
        self.vel_iters = 8
        self.pos_iters = 3

    def step(self):
        """物理シミュレーションを1ステップ進める"""
        self.world.Step(self.time_step, self.vel_iters, self.pos_iters)

    def add_static_polygon(self, vertices: List[Vec2]) -> b2Body:
        """静的なポリゴン（壁）を追加"""
        body = self.world.CreateStaticBody(
            shapes=b2PolygonShape(vertices=vertices)
        )
        return body
```

---

## 3. 強化学習 (`src/rl/`)

### 3.1 Policy Network (policy.py)

観測から行動への写像。

```python
class GaussianPolicy(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int, hidden_sizes: List[int] = [256, 256]):
        super().__init__()

        # 共有エンコーダ
        self.encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_sizes[0]),
            nn.ReLU(),
            nn.Linear(hidden_sizes[0], hidden_sizes[1]),
            nn.ReLU(),
        )

        # 平均と対数標準偏差
        self.mean_head = nn.Linear(hidden_sizes[1], action_dim)
        self.log_std_head = nn.Linear(hidden_sizes[1], action_dim)

    def forward(self, obs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            mean, log_std
        """
        features = self.encoder(obs)
        mean = self.mean_head(features)
        log_std = self.log_std_head(features)
        log_std = torch.clamp(log_std, -20, 2)  # 安定化
        return mean, log_std

    def sample(self, obs: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            action, log_prob
        """
        mean, log_std = self.forward(obs)
        std = torch.exp(log_std)
        dist = Normal(mean, std)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum(dim=-1)
        return action, log_prob
```

### 3.2 Value Network (value.py)

状態価値関数。

```python
class ValueNetwork(nn.Module):
    def __init__(self, obs_dim: int, hidden_sizes: List[int] = [256, 256]):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(obs_dim, hidden_sizes[0]),
            nn.ReLU(),
            nn.Linear(hidden_sizes[0], hidden_sizes[1]),
            nn.ReLU(),
            nn.Linear(hidden_sizes[1], 1),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.network(obs).squeeze(-1)
```

### 3.3 PPO Algorithm (ppo.py)

```python
class PPO:
    def __init__(self, policy: GaussianPolicy, value: ValueNetwork, config: dict):
        self.policy = policy
        self.value = value

        self.lr = config['learning_rate']
        self.clip_ratio = config['clip_ratio']
        self.entropy_coef = config['entropy_coef']
        self.value_coef = config['value_coef']

        self.optimizer = Adam([
            {'params': policy.parameters()},
            {'params': value.parameters()},
        ], lr=self.lr)

    def update(self, buffer: RolloutBuffer) -> dict:
        """
        PPO更新を実行

        Returns:
            統計情報（損失等）
        """
        for epoch in range(self.num_epochs):
            for batch in buffer.get_batches(self.batch_size):
                # 現在のポリシーでログ確率を計算
                _, new_log_probs = self.policy.sample(batch.obs)

                # Advantage
                advantages = batch.returns - batch.values
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

                # Policy loss (PPO clip)
                ratio = torch.exp(new_log_probs - batch.log_probs)
                surr1 = ratio * advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_ratio, 1 + self.clip_ratio) * advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                # Value loss
                values_pred = self.value(batch.obs)
                value_loss = F.mse_loss(values_pred, batch.returns)

                # Entropy bonus
                entropy = ... # 計算

                # Total loss
                loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy

                # 更新
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.policy.parameters(), max_norm=0.5)
                self.optimizer.step()
```

### 3.4 Rollout Buffer (buffer.py)

```python
class RolloutBuffer:
    def __init__(self, capacity: int, obs_dim: int, action_dim: int, gamma: float, gae_lambda: float):
        self.observations = np.zeros((capacity, obs_dim))
        self.actions = np.zeros((capacity, action_dim))
        self.rewards = np.zeros(capacity)
        self.values = np.zeros(capacity)
        self.log_probs = np.zeros(capacity)
        self.dones = np.zeros(capacity)

        self.gamma = gamma
        self.gae_lambda = gae_lambda

    def add(self, obs, action, reward, value, log_prob, done):
        """経験を追加"""

    def compute_returns_and_advantages(self, last_value: float):
        """GAEを使ってリターンとAdvantageを計算"""
        advantages = np.zeros_like(self.rewards)
        last_gae = 0

        for t in reversed(range(len(self.rewards))):
            if t == len(self.rewards) - 1:
                next_value = last_value
            else:
                next_value = self.values[t + 1]

            delta = self.rewards[t] + self.gamma * next_value * (1 - self.dones[t]) - self.values[t]
            advantages[t] = last_gae = delta + self.gamma * self.gae_lambda * (1 - self.dones[t]) * last_gae

        returns = advantages + self.values
        return returns, advantages
```

---

## 4. カリキュラム学習 (`src/curriculum/`)

### 4.1 Curriculum Manager

```python
class CurriculumManager:
    def __init__(self, courses: List[str], success_threshold: float = 0.8):
        self.courses = courses  # 易→難の順
        self.current_level = 0
        self.success_threshold = success_threshold
        self.recent_success_rate = deque(maxlen=100)

    def update(self, success: bool):
        """エピソード結果を記録"""
        self.recent_success_rate.append(success)

    def should_advance(self) -> bool:
        """次のレベルに進むべきか判定"""
        if len(self.recent_success_rate) < 50:
            return False
        success_rate = np.mean(self.recent_success_rate)
        return success_rate >= self.success_threshold

    def advance_level(self):
        """次のレベルに進む"""
        if self.current_level < len(self.courses) - 1:
            self.current_level += 1
            self.recent_success_rate.clear()
```

---

## 5. Domain Randomization (`src/domain_randomization/`)

### 5.1 Physics Randomizer

```python
class PhysicsRandomizer:
    def __init__(self, config: dict):
        self.friction_range = config.get('friction_range', (0.5, 1.5))
        self.mass_range = config.get('mass_range', (0.8, 1.2))
        self.motor_delay_range = config.get('motor_delay_range', (0, 0.05))

    def randomize(self, vehicle: Vehicle):
        """車両パラメータをランダム化"""
        vehicle.friction = np.random.uniform(*self.friction_range)
        vehicle.mass = np.random.uniform(*self.mass_range)
        vehicle.motor_delay = np.random.uniform(*self.motor_delay_range)
```

---

## 6. ユーティリティ (`src/utils/`)

### 6.1 Config Manager

```python
class ConfigManager:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def get(self, key: str, default=None):
        return self.config.get(key, default)
```

### 6.2 Logger

```python
class TensorBoardLogger:
    def __init__(self, log_dir: str):
        self.writer = SummaryWriter(log_dir)

    def log_scalar(self, tag: str, value: float, step: int):
        self.writer.add_scalar(tag, value, step)

    def log_histogram(self, tag: str, values: np.ndarray, step: int):
        self.writer.add_histogram(tag, values, step)
```

---

## 7. 実行スクリプト (`scripts/`)

### 7.1 Training Script

```python
# scripts/train.py
def main(config_path: str):
    # 設定ロード
    config = ConfigManager(config_path)

    # 環境作成
    env = MinicarEnv(config.get('env'))

    # エージェント作成
    policy = GaussianPolicy(...)
    value = ValueNetwork(...)
    ppo = PPO(policy, value, config.get('ppo'))

    # カリキュラムマネージャー
    curriculum = CurriculumManager(config.get('courses'))

    # 学習ループ
    for episode in range(num_episodes):
        obs, _ = env.reset()
        done = False

        while not done:
            action, log_prob = policy.sample(obs)
            next_obs, reward, terminated, truncated, info = env.step(action)
            # バッファに保存
            ...

        # PPO更新
        if episode % update_interval == 0:
            ppo.update(buffer)
```

---

## まとめ

各コンポーネントは独立して開発・テスト可能な設計になっています。Phase 1では基盤となる`env`, `physics`モジュールを実装し、Phase 2で`rl`モジュールを統合します。
