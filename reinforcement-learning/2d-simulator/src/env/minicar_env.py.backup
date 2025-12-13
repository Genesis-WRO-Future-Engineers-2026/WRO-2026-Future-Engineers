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

# Domain Randomization
from src.domain_randomization.physics_randomizer import (
    PhysicsRandomizer,
    PhysicsRandomizationConfig,
)
from src.domain_randomization.sensor_noise import (
    SensorNoiseRandomizer,
    SensorNoiseConfig,
)

# Adaptive Reward Scaling
from src.rl.adaptive_reward import AdaptiveRewardScaler, RewardCoefficients


class MinicarEnv(gym.Env):
    """ミニカーレースのGym互換環境"""

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    # 衝突判定パラメータ
    # NOTE: 衝突判定はBox2Dの物理エンジンで行うため、距離ベースの閾値は不要
    # WALL_APPROACH_DISTANCEは報酬設計で壁接近ペナルティを与えるために使用
    WALL_APPROACH_DISTANCE = 0.3  # 壁接近ペナルティの閾値（m）
    COLLISION_PENALTY = -100.0  # 衝突時の報酬ペナルティ

    def __init__(
        self,
        course_file: str = "courses/easy/simple_oval.json",
        render_mode: Optional[str] = None,
        max_steps: int = 2000,
        deployment_mode: bool = False,
        # Domain Randomization用の追加パラメータ
        enable_domain_randomization: bool = False,
        physics_randomization_config: Optional[PhysicsRandomizationConfig] = None,
        sensor_noise_config: Optional[SensorNoiseConfig] = None,
        # Adaptive Reward Scaling用のパラメータ
        adaptive_reward_scaler: Optional[AdaptiveRewardScaler] = None,
    ):
        """
        Args:
            course_file: コース定義ファイル
            render_mode: 描画モード ('human', 'rgb_array', None)
            max_steps: 最大ステップ数
            deployment_mode: 本番環境モード（ゴール到達で終了しない）
            enable_domain_randomization: Domain Randomizationを有効化
            physics_randomization_config: 物理ランダム化の設定
            sensor_noise_config: センサーノイズの設定
            adaptive_reward_scaler: 適応的報酬スケーラー
        """
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps
        self.deployment_mode = deployment_mode

        # Domain Randomization設定
        self.enable_domain_randomization = enable_domain_randomization

        if self.enable_domain_randomization:
            # 物理ランダム化
            if physics_randomization_config is not None:
                self.physics_randomizer = PhysicsRandomizer(physics_randomization_config)
            else:
                # デフォルト設定を使用
                from src.domain_randomization.physics_randomizer import DEFAULT_PHYSICS_CONFIG
                self.physics_randomizer = PhysicsRandomizer(DEFAULT_PHYSICS_CONFIG)

            # センサーノイズ
            if sensor_noise_config is not None:
                self.sensor_noise_randomizer = SensorNoiseRandomizer(sensor_noise_config)
            else:
                # デフォルト設定を使用
                from src.domain_randomization.sensor_noise import DEFAULT_SENSOR_NOISE_CONFIG
                self.sensor_noise_randomizer = SensorNoiseRandomizer(DEFAULT_SENSOR_NOISE_CONFIG)

            print("[INFO] Domain Randomization enabled")
        else:
            self.physics_randomizer = None
            self.sensor_noise_randomizer = None

        # Adaptive Reward Scaler
        self.adaptive_reward_scaler = adaptive_reward_scaler

        # コースのロード
        self.course = Course(course_file)

        # 衝突検出リスナーを作成
        self.collision_listener = CollisionListener()

        # 物理世界（ContactListenerを登録）
        self.world = PhysicsWorld(collision_listener=self.collision_listener)

        # 壁の作成
        self.course.create_walls(self.world.world)

        # 車両
        start_pos, start_angle = self.course.get_start_pose()
        self.vehicle = Vehicle(self.world.world, start_pos, start_angle)

        # LiDARセンサー（前方120度カバー: -60° ~ +60°）
        self.lidar = LiDARSensor(
            self.world.world,
            num_rays=5,
            max_range=LIDAR_MAX_RANGE,
            angle_min=-np.pi/3,  # -60度
            angle_max=np.pi/3    # +60度
        )

        # レンダラー
        self.renderer = None
        if render_mode == "human":
            self.renderer = Renderer()
            print(f"[DEBUG] Renderer initialized in {render_mode} mode")

        # 行動空間: [steering, throttle]
        # steering: -1.0 (左) ~ 1.0 (右)
        # throttle: -1.0 (後退) ~ 1.0 (前進)
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0]),
            high=np.array([1.0, 1.0]),
            dtype=np.float32,
        )

        # 観測空間: LiDAR(5) + velocity(2) + angular_velocity(1) + last_action(2) = 10
        # NOTE: チェックポイント情報は含めない（Sim2Real対応）
        # チェックポイントは報酬計算でのみ使用
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32
        )

        # 状態
        self.step_count = 0
        self.last_action = np.zeros(2)
        self.total_reward = 0.0
        self.next_checkpoint_index = 0  # 次に通過すべきチェックポイントのインデックス
        self.is_collision = False  # 衝突フラグ

        # LiDARスキャンと車両状態のキャッシュ（パフォーマンス最適化）
        self._cached_lidar_scan = None
        self._cached_vehicle_state = None

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        環境をリセット

        Returns:
            observation, info
        """
        super().reset(seed=seed)

        # Domain Randomization: 物理パラメータをランダム化
        if self.enable_domain_randomization and self.physics_randomizer:
            physics_params = self.physics_randomizer.randomize()
        else:
            physics_params = {}

        # 車両をリセット（ランダム化されたパラメータで）
        start_pos, start_angle = self.course.get_start_pose()

        if physics_params:
            self.vehicle.reset(
                start_pos,
                start_angle,
                mass=physics_params.get('mass'),
                friction=physics_params.get('friction'),
                linear_damping=physics_params.get('linear_damping'),
                angular_damping=physics_params.get('angular_damping'),
                max_motor_force=physics_params.get('motor_force'),
                max_lateral_impulse=physics_params.get('max_lateral_impulse'),
            )
        else:
            self.vehicle.reset(start_pos, start_angle)

        # 状態をリセット
        self.step_count = 0
        self.last_action = np.zeros(2)
        self.total_reward = 0.0
        self.next_checkpoint_index = 0  # 次のチェックポイントをリセット
        self.is_collision = False  # 衝突フラグをリセット

        # 衝突検出リスナーをリセット
        self.world.reset_collision()

        # キャッシュを初期化
        state = self.vehicle.get_state()
        self._cached_vehicle_state = state
        self._cached_lidar_scan = self.lidar.scan(state["position"], state["angle"])

        # 初期観測
        obs = self._get_observation()
        info = self._get_info()

        return obs, info

    def step(
        self, action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        1ステップ実行

        Args:
            action: [steering, throttle]

        Returns:
            observation, reward, terminated, truncated, info
        """
        # 行動を適用
        steering = float(action[0])
        throttle = float(action[1])
        self.vehicle.apply_control(steering, throttle)

        # 物理シミュレーション
        self.world.step()

        # 車両状態とLiDARスキャンをキャッシュ（1回のみ実行）
        self._cached_vehicle_state = self.vehicle.get_state()
        self._cached_lidar_scan = self.lidar.scan(
            self._cached_vehicle_state["position"],
            self._cached_vehicle_state["angle"]
        )

        # 観測（キャッシュを使用）
        obs = self._get_observation()

        # 報酬計算（キャッシュを使用）
        reward = self._compute_reward()
        self.total_reward += reward

        # 終了判定（キャッシュを使用）
        terminated = self._check_terminated()
        truncated = self.step_count >= self.max_steps

        # 情報（キャッシュを使用）
        info = self._get_info()

        # 状態更新
        self.last_action = action
        self.step_count += 1

        return obs, reward, terminated, truncated, info

    def _get_observation(self) -> np.ndarray:
        """
        現在の観測を取得

        Returns:
            観測ベクトル (10次元)

        NOTE: Sim2Real対応のため、チェックポイント情報は含めない。
        チェックポイントは報酬計算でのみ使用し、エージェントは
        LiDARと速度情報だけで走行を学習する。
        """
        # キャッシュされたデータを使用
        lidar_scan = self._cached_lidar_scan.copy()

        # Domain Randomization: センサーノイズを適用
        if self.enable_domain_randomization and self.sensor_noise_randomizer:
            lidar_scan = self.sensor_noise_randomizer.apply_noise(
                self.lidar,
                lidar_scan
            )

        # LiDARの正規化
        lidar_normalized = lidar_scan / LIDAR_MAX_RANGE

        velocity = np.array(self._cached_vehicle_state["velocity"])
        angular_velocity = np.array([self._cached_vehicle_state["angular_velocity"]])

        # 観測を結合（チェックポイント情報は含めない）
        obs = np.concatenate(
            [
                lidar_normalized,  # 5
                velocity / 3.0,  # 2（正規化）
                angular_velocity / 5.0,  # 1（正規化）
                self.last_action,  # 2
            ]
        )

        return obs.astype(np.float32)

    def _compute_reward(self) -> float:
        """
        報酬を計算（適応的報酬スケーリング対応）

        Returns:
            報酬

        設計方針:
        - シンプルであること（必要最小限の5項目）
        - 矛盾がないこと（時間ペナルティで早さを奨励）
        - タスクの本質: 壁にぶつからず、なるべく早く、ゴールに到達
        - 適応的スケーリング: 学習の進捗に応じて係数を自動調整

        詳細: src/env/REWARD_DESIGN.md 参照
        """
        reward = 0.0
        # キャッシュされたデータを使用
        state = self._cached_vehicle_state
        lidar_scan = self._cached_lidar_scan

        # 適応的報酬スケーリングが有効な場合は係数を取得、そうでない場合はv3.2のデフォルト値
        if self.adaptive_reward_scaler is not None:
            coeffs = self.adaptive_reward_scaler.get_coefficients()
        else:
            # v3.2のデフォルト係数
            coeffs = RewardCoefficients(
                time_penalty=0.7,
                direction_reward_scale=0.7,
                checkpoint_reward=200.0,
                goal_reward=500.0,
                collision_penalty=-100.0,
                time_bonus_scale=2.0,
            )

        # 1. 時間ペナルティ（早くゴールするインセンティブ）
        reward -= coeffs.time_penalty

        # 2. チェックポイント方向報酬（正しい方向へのガイダンス）
        checkpoints = self.course.get_checkpoints()
        if self.next_checkpoint_index < len(checkpoints):
            # 次のチェックポイントまでの距離を計算
            cp_pos = checkpoints[self.next_checkpoint_index]["position"]
            distance_to_cp = np.linalg.norm(
                np.array(state["position"]) - np.array(cp_pos)
            )
            # 距離が近いほど高報酬（遠くても報酬あり）
            max_distance = 20.0  # コースサイズに応じて調整
            normalized_distance = min(distance_to_cp, max_distance)
            # 適応的スケーリング係数を使用
            reward += (max_distance - normalized_distance) / max_distance * coeffs.direction_reward_scale

            # 2.1. チェックポイント通過報酬
            if self.course.check_checkpoint(state["position"], self.next_checkpoint_index):
                reward += coeffs.checkpoint_reward
                self.next_checkpoint_index += 1  # 次へ進む
        else:
            # 全チェックポイント通過後、ゴール方向報酬
            goal_pos, _ = self.course.get_goal_info()
            distance_to_goal = np.linalg.norm(
                np.array(state["position"]) - np.array(goal_pos)
            )
            max_distance = 20.0
            normalized_distance = min(distance_to_goal, max_distance)
            # 適応的スケーリング係数を使用
            reward += (max_distance - normalized_distance) / max_distance * coeffs.direction_reward_scale

        # 3. ゴール到達報酬（最終目標の達成）
        if self.course.check_goal(state["position"]):
            # 全チェックポイントを順番に通過している場合のみ
            if self.next_checkpoint_index == len(checkpoints):
                # 基本ゴール報酬
                reward += coeffs.goal_reward
                # 時間ボーナス（早くゴールするほど高報酬）
                remaining_steps = self.max_steps - self.step_count
                time_bonus = remaining_steps * coeffs.time_bonus_scale
                reward += time_bonus

        # 4. 衝突ペナルティ（壁にぶつからない）
        if self.world.has_collision():
            reward += coeffs.collision_penalty

        return reward

    def _check_terminated(self) -> bool:
        """
        終了条件をチェック

        Returns:
            終了したかどうか

        NOTE: deployment_mode=True の場合、ゴール到達では終了しない
        - 学習モード: ゴール到達・衝突で終了
        - 本番モード: 衝突のみ終了（リスタート用）、ゴール到達は継続
        """
        # キャッシュされたデータを使用
        state = self._cached_vehicle_state

        # 本番環境モード: 衝突のみ終了判定
        if self.deployment_mode:
            if self.world.has_collision():
                self.is_collision = True
                return True
            return False

        # 学習モード: ゴール到達で終了
        checkpoints = self.course.get_checkpoints()
        all_checkpoints_passed = self.next_checkpoint_index == len(checkpoints)
        if all_checkpoints_passed and self.course.check_goal(state["position"]):
            return True

        # 壁衝突（Box2Dの物理衝突検出を使用）
        if self.world.has_collision():
            self.is_collision = True  # 衝突フラグを立てる
            return True

        return False

    def _get_info(self) -> Dict[str, Any]:
        """
        追加情報を取得

        Returns:
            情報の辞書
        """
        # キャッシュされたデータを使用
        state = self._cached_vehicle_state
        lidar_scan = self._cached_lidar_scan

        checkpoints = self.course.get_checkpoints()
        return {
            "position": state["position"],
            "speed": state["speed"],
            "angle": state["angle"],
            "step_count": self.step_count,
            "total_reward": self.total_reward,
            "next_checkpoint_index": self.next_checkpoint_index,
            "total_checkpoints": len(checkpoints),
            "checkpoints_remaining": len(checkpoints) - self.next_checkpoint_index,
            "min_distance": np.min(lidar_scan),
            "is_collision": self.is_collision,  # 衝突フラグ
        }

    def render(self):
        """環境を描画"""
        if self.render_mode != "human":
            return

        if self.renderer is None:
            print("[DEBUG] Renderer was None, creating new Renderer")
            self.renderer = Renderer()

        # 画面クリア
        self.renderer.clear()

        # キャッシュされたデータを使用
        state = self._cached_vehicle_state
        lidar_scan = self._cached_lidar_scan

        # カメラを車両に追従
        self.renderer.set_camera(state["position"][0], state["position"][1])

        # 壁を描画
        self.renderer.draw_walls(self.course.walls)

        # チェックポイントを描画
        checkpoints = self.course.get_checkpoints()
        for i, cp in enumerate(checkpoints):
            if i >= self.next_checkpoint_index:
                # まだ通過していないチェックポイントのみ描画
                self.renderer.draw_checkpoint(
                    tuple(cp["position"]), cp.get("radius", 1.0)
                )

        # ゴールを描画
        goal_pos, goal_radius = self.course.get_goal_info()
        self.renderer.draw_goal(goal_pos, goal_radius)

        # LiDARを描画（キャッシュを使用）
        self.renderer.draw_lidar(
            state["position"],
            state["angle"],
            lidar_scan,
            num_rays=5,
            angle_min=-np.pi/3,  # -60度
            angle_max=np.pi/3    # +60度
        )

        # 車両を描画
        self.renderer.draw_vehicle(self.vehicle)

        # デバッグ情報
        info = self._get_info()
        debug_info = {
            "Speed": info["speed"],
            "Step": info["step_count"],
            "Reward": info["total_reward"],
            "CPs": f"{info['next_checkpoint_index']}/{info['total_checkpoints']}",
            "Min Dist": info["min_distance"],
        }
        self.renderer.draw_debug_info(debug_info)

        # 画面更新
        should_continue = self.renderer.update()
        if not should_continue:
            # ユーザーがウィンドウを閉じた場合
            self.close()

    def close(self):
        """リソースを解放"""
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None

    def load_course(self, course_file: str):
        """
        新しいコースをロードする（カリキュラム学習用）

        Args:
            course_file: コース定義ファイル
        """
        # 現在のコースファイルと同じ場合はスキップ
        if hasattr(self, 'course') and self.course.course_file == course_file:
            return

        # 衝突検出リスナーをリセット
        self.collision_listener.reset()

        # 物理世界をリセット（同じリスナーを再利用）
        self.world = PhysicsWorld(collision_listener=self.collision_listener)

        # 新しいコースをロード
        self.course = Course(course_file)

        # 壁を作成
        self.course.create_walls(self.world.world)

        # 車両を再作成
        start_pos, start_angle = self.course.get_start_pose()
        self.vehicle = Vehicle(self.world.world, start_pos, start_angle)

        # LiDARセンサーを再作成（前方120度カバー: -60° ~ +60°）
        self.lidar = LiDARSensor(
            self.world.world,
            num_rays=5,
            max_range=LIDAR_MAX_RANGE,
            angle_min=-np.pi/3,  # -60度
            angle_max=np.pi/3    # +60度
        )

        # 状態をリセット
        self.step_count = 0
        self.last_action = np.zeros(2)
        self.total_reward = 0.0
        self.next_checkpoint_index = 0  # 次のチェックポイントをリセット
        self.is_collision = False  # 衝突フラグをリセット
        self._cached_lidar = None

        print(f"[INFO] Loaded new course: {course_file}")
