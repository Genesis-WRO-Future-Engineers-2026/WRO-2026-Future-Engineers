"""Gym互換のミニカー環境（リファクタリング版）"""

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

# リファクタリング後のモジュール
from src.env.observation import ObservationBuilder, ObservationConfig
from src.env.termination import TerminationChecker
from src.env.randomization import RandomizationManager
from src.env.reward.factory import RewardFactory
from src.env.reward.base import RewardContext


class MinicarEnv(gym.Env):
    """ミニカーレースのGym互換環境（リファクタリング版）

    単一責任原則に基づき、各責務を専用モジュールに委譲:
    - 報酬計算: RewardFactory + CompositeReward
    - 観測構築: ObservationBuilder
    - 終了判定: TerminationChecker
    - Domain Randomization: RandomizationManager
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

    def __init__(
        self,
        course_file: str = "courses/easy/simple_oval.json",
        render_mode: Optional[str] = None,
        max_steps: int = 2000,
        deployment_mode: bool = False,
        # Domain Randomization
        enable_domain_randomization: bool = False,
        physics_randomization_config=None,
        sensor_noise_config=None,
        # Adaptive Reward Scaling
        adaptive_reward_scaler=None,
        # リファクタリング後の依存性注入（オプション）
        observation_builder: Optional[ObservationBuilder] = None,
        termination_checker: Optional[TerminationChecker] = None,
        randomization_manager: Optional[RandomizationManager] = None,
        reward_function=None,  # CompositeReward
    ):
        """
        Args:
            course_file: コース定義ファイル
            render_mode: 描画モード
            max_steps: 最大ステップ数
            deployment_mode: 本番環境モード
            enable_domain_randomization: Domain Randomization有効化
            physics_randomization_config: 物理ランダム化設定
            sensor_noise_config: センサーノイズ設定
            adaptive_reward_scaler: 適応的報酬スケーラー
            observation_builder: 観測ビルダー（Noneの場合はデフォルト作成）
            termination_checker: 終了条件チェッカー（Noneの場合はデフォルト作成）
            randomization_manager: ランダム化マネージャー（Noneの場合は設定から作成）
            reward_function: 報酬関数（Noneの場合はデフォルト作成）
        """
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps
        self.deployment_mode = deployment_mode

        # Domain Randomization管理
        if randomization_manager is not None:
            self.randomization_manager = randomization_manager
        else:
            self.randomization_manager = RandomizationManager(
                enabled=enable_domain_randomization,
                physics_config=physics_randomization_config,
                sensor_noise_config=sensor_noise_config,
            )

        # 観測ビルダー
        if observation_builder is not None:
            self.obs_builder = observation_builder
        else:
            self.obs_builder = ObservationBuilder(
                config=ObservationConfig(),
                sensor_noise_randomizer=self.randomization_manager.get_sensor_noise_randomizer(),
            )

        # 終了条件チェッカー
        if termination_checker is not None:
            self.termination_checker = termination_checker
        else:
            self.termination_checker = TerminationChecker(deployment_mode=deployment_mode)

        # 報酬関数
        if reward_function is not None:
            self.reward_fn = reward_function
        else:
            self.reward_fn = RewardFactory.create_default_reward(
                adaptive_scaler=adaptive_reward_scaler
            )

        # コースのロード
        self.course = Course(course_file)

        # 衝突検出リスナー
        self.collision_listener = CollisionListener()

        # 物理世界
        self.world = PhysicsWorld(collision_listener=self.collision_listener)

        # 壁の作成
        self.course.create_walls(self.world.world)

        # 車両
        start_pos, start_angle = self.course.get_start_pose()
        self.vehicle = Vehicle(self.world.world, start_pos, start_angle)

        # LiDARセンサー
        self.lidar = LiDARSensor(
            self.world.world,
            num_rays=5,
            max_range=LIDAR_MAX_RANGE,
            angle_min=-np.pi/3,
            angle_max=np.pi/3
        )

        # レンダラー
        self.renderer = None
        if render_mode == "human":
            self.renderer = Renderer()

        # 行動空間
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0]),
            high=np.array([1.0, 1.0]),
            dtype=np.float32,
        )

        # 観測空間
        obs_shape = self.obs_builder.get_observation_space_shape()
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=obs_shape, dtype=np.float32
        )

        # 状態
        self.step_count = 0
        self.last_action = np.zeros(2)
        self.total_reward = 0.0
        self.next_checkpoint_index = 0
        self.is_collision = False

        # キャッシュ
        self._cached_lidar_scan = None
        self._cached_vehicle_state = None

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """環境をリセット"""
        super().reset(seed=seed)

        # Domain Randomization: 物理パラメータをランダム化
        physics_params = self.randomization_manager.randomize_physics()

        # 車両をリセット
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
        self.next_checkpoint_index = 0
        self.is_collision = False

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
        """1ステップ実行"""
        # 行動を適用
        steering = float(action[0])
        throttle = float(action[1])
        self.vehicle.apply_control(steering, throttle)

        # 物理シミュレーション
        self.world.step()

        # 車両状態とLiDARスキャンをキャッシュ
        self._cached_vehicle_state = self.vehicle.get_state()
        self._cached_lidar_scan = self.lidar.scan(
            self._cached_vehicle_state["position"],
            self._cached_vehicle_state["angle"]
        )

        # 観測
        obs = self._get_observation()

        # 報酬計算
        reward, checkpoint_passed = self._compute_reward()
        self.total_reward += reward

        # チェックポイント通過時のインデックス更新
        if checkpoint_passed:
            self.next_checkpoint_index += 1

        # 終了判定
        terminated, collision = self._check_terminated()
        if collision:
            self.is_collision = True

        truncated = self.step_count >= self.max_steps

        # 情報
        info = self._get_info()

        # 状態更新
        self.last_action = action
        self.step_count += 1

        return obs, reward, terminated, truncated, info

    def _get_observation(self) -> np.ndarray:
        """観測を取得（ObservationBuilderに委譲）"""
        return self.obs_builder.build(
            lidar_scan=self._cached_lidar_scan,
            vehicle_state=self._cached_vehicle_state,
            last_action=self.last_action,
            lidar_sensor=self.lidar,
        )

    def _compute_reward(self) -> Tuple[float, bool]:
        """報酬を計算（CompositeRewardに委譲）"""
        # 報酬コンテキストを構築
        context = RewardContext(
            position=self._cached_vehicle_state["position"],
            velocity=self._cached_vehicle_state["velocity"],
            speed=self._cached_vehicle_state["speed"],
            angle=self._cached_vehicle_state["angle"],
            angular_velocity=self._cached_vehicle_state["angular_velocity"],
            lidar_scan=self._cached_lidar_scan,
            action=self.last_action,
            checkpoints=self.course.get_checkpoints(),
            next_checkpoint_index=self.next_checkpoint_index,
            goal_position=self.course.get_goal_info()[0],
            goal_radius=self.course.get_goal_info()[1],
            step_count=self.step_count,
            max_steps=self.max_steps,
            has_collision=self.world.has_collision(),
            deployment_mode=self.deployment_mode,
        )

        # 報酬を計算（checkpoint_passedフラグも取得）
        reward, checkpoint_passed = self.reward_fn.compute(context, self.course)

        return reward, checkpoint_passed

    def _check_terminated(self) -> Tuple[bool, bool]:
        """終了条件をチェック（TerminationCheckerに委譲）"""
        return self.termination_checker.check(
            vehicle_position=self._cached_vehicle_state["position"],
            has_collision=self.world.has_collision(),
            next_checkpoint_index=self.next_checkpoint_index,
            total_checkpoints=len(self.course.get_checkpoints()),
            course=self.course,
        )

    def _get_info(self) -> Dict[str, Any]:
        """追加情報を取得"""
        checkpoints = self.course.get_checkpoints()
        return {
            "position": self._cached_vehicle_state["position"],
            "speed": self._cached_vehicle_state["speed"],
            "angle": self._cached_vehicle_state["angle"],
            "step_count": self.step_count,
            "total_reward": self.total_reward,
            "next_checkpoint_index": self.next_checkpoint_index,
            "total_checkpoints": len(checkpoints),
            "checkpoints_remaining": len(checkpoints) - self.next_checkpoint_index,
            "min_distance": np.min(self._cached_lidar_scan),
            "is_collision": self.is_collision,
        }

    def render(self):
        """環境を描画"""
        if self.render_mode != "human":
            return

        if self.renderer is None:
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

        # LiDARを描画
        self.renderer.draw_lidar(
            state["position"],
            state["angle"],
            lidar_scan,
            num_rays=5,
            angle_min=-np.pi/3,
            angle_max=np.pi/3
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
            self.close()

    def close(self):
        """リソースを解放"""
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None

    def load_course(self, course_file: str):
        """新しいコースをロード（カリキュラム学習用）

        Args:
            course_file: コース定義ファイル
        """
        # 現在のコースファイルと同じ場合はスキップ
        if hasattr(self, 'course') and self.course.course_file == course_file:
            return

        # 衝突検出リスナーをリセット
        self.collision_listener.reset()

        # 物理世界をリセット
        self.world = PhysicsWorld(collision_listener=self.collision_listener)

        # 新しいコースをロード
        self.course = Course(course_file)

        # 壁を作成
        self.course.create_walls(self.world.world)

        # 車両を再作成
        start_pos, start_angle = self.course.get_start_pose()
        self.vehicle = Vehicle(self.world.world, start_pos, start_angle)

        # LiDARセンサーを再作成
        self.lidar = LiDARSensor(
            self.world.world,
            num_rays=5,
            max_range=LIDAR_MAX_RANGE,
            angle_min=-np.pi/3,
            angle_max=np.pi/3
        )

        # 状態をリセット
        self.step_count = 0
        self.last_action = np.zeros(2)
        self.total_reward = 0.0
        self.next_checkpoint_index = 0
        self.is_collision = False
        self._cached_lidar_scan = None
        self._cached_vehicle_state = None

        print(f"[INFO] Loaded new course: {course_file}")
