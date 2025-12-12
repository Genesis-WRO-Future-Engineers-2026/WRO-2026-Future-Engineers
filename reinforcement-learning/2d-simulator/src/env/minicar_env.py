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
    ):
        """
        Args:
            course_file: コース定義ファイル
            render_mode: 描画モード ('human', 'rgb_array', None)
            max_steps: 最大ステップ数
        """
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps

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
        lidar_scan = self._cached_lidar_scan
        velocity = np.array(self._cached_vehicle_state["velocity"])
        angular_velocity = np.array([self._cached_vehicle_state["angular_velocity"]])

        # 観測を結合（チェックポイント情報は含めない）
        obs = np.concatenate(
            [
                lidar_scan,  # 5
                velocity,  # 2
                angular_velocity,  # 1
                self.last_action,  # 2
            ]
        )

        return obs.astype(np.float32)

    def _compute_reward(self) -> float:
        """
        報酬を計算

        Returns:
            報酬
        """
        reward = 0.0
        # キャッシュされたデータを使用
        state = self._cached_vehicle_state
        lidar_scan = self._cached_lidar_scan

        # 1. 速度報酬（速く走ることを奨励）
        speed = state["speed"]
        reward += speed * 0.05

        # 2. 時間ペナルティ（早くゴールすることを奨励）
        reward -= 0.3

        # 3. 壁接近ペナルティ
        min_distance = np.min(lidar_scan)
        if min_distance < self.WALL_APPROACH_DISTANCE:
            reward -= (self.WALL_APPROACH_DISTANCE - min_distance) * 10

        # 3.5. 衝突ペナルティ（Box2D物理衝突検出を使用）
        if self.world.has_collision():
            reward += self.COLLISION_PENALTY  # 大きなペナルティ

        # 4. チェックポイント報酬（順序通りに通過する必要がある）
        checkpoints = self.course.get_checkpoints()
        if self.next_checkpoint_index < len(checkpoints):
            # 次のチェックポイントのみ判定
            if self.course.check_checkpoint(state["position"], self.next_checkpoint_index):
                reward += 100.0
                self.next_checkpoint_index += 1  # 次へ進む

        # 5. ゴール到達 + 時間ボーナス（早くゴールするほど高い報酬）
        if self.course.check_goal(state["position"]):
            # 全チェックポイントを順番に通過している場合のみゴール報酬
            if self.next_checkpoint_index == len(checkpoints):
                # 基本ゴール報酬
                reward += 500.0
                # 時間ボーナス（早いほど高い）
                remaining_steps = self.max_steps - self.step_count
                time_bonus = remaining_steps * 1.5
                reward += time_bonus

        return reward

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
