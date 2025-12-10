"""Gym互換のミニカー環境"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Optional, Any

from src.physics.box2d_wrapper import PhysicsWorld
from src.env.vehicle import Vehicle
from src.env.sensors import LiDARSensor
from src.env.course import Course
from src.env.renderer import Renderer


class MinicarEnv(gym.Env):
    """ミニカーレースのGym互換環境"""

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 30}

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

        # 物理世界
        self.world = PhysicsWorld()

        # 壁の作成
        self.course.create_walls(self.world.world)

        # 車両
        start_pos, start_angle = self.course.get_start_pose()
        self.vehicle = Vehicle(self.world.world, start_pos, start_angle)

        # LiDARセンサー
        self.lidar = LiDARSensor(self.world.world, num_rays=72, max_range=10.0)

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

        # 観測空間: LiDAR(72) + velocity(2) + angular_velocity(1) + last_action(2) = 77
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(77,), dtype=np.float32
        )

        # 状態
        self.step_count = 0
        self.last_action = np.zeros(2)
        self.total_reward = 0.0
        self.checkpoints_passed = set()

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
        self.checkpoints_passed = set()

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
            観測ベクトル (77次元)
        """
        # キャッシュされたデータを使用
        lidar_scan = self._cached_lidar_scan
        velocity = np.array(self._cached_vehicle_state["velocity"])
        angular_velocity = np.array([self._cached_vehicle_state["angular_velocity"]])

        # 観測を結合
        obs = np.concatenate(
            [
                lidar_scan,  # 72
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

        # 1. 速度報酬
        speed = state["speed"]
        reward += speed * 0.1

        # 2. 時間ペナルティ
        reward -= 0.01

        # 3. 壁接近ペナルティ
        min_distance = np.min(lidar_scan)
        if min_distance < 0.3:
            reward -= (0.3 - min_distance) * 10

        # 4. チェックポイント報酬
        checkpoints = self.course.get_checkpoints()
        for i, checkpoint in enumerate(checkpoints):
            if i not in self.checkpoints_passed:
                if self.course.check_checkpoint(state["position"], i):
                    self.checkpoints_passed.add(i)
                    reward += 50.0

        # 5. ゴール到達
        if self.course.check_goal(state["position"]):
            reward += 500.0

        return reward

    def _check_terminated(self) -> bool:
        """
        終了条件をチェック

        Returns:
            終了したかどうか
        """
        # キャッシュされたデータを使用
        state = self._cached_vehicle_state
        lidar_scan = self._cached_lidar_scan

        # ゴール到達（すべてのチェックポイントを通過している必要がある）
        checkpoints = self.course.get_checkpoints()
        all_checkpoints_passed = len(self.checkpoints_passed) == len(checkpoints)
        if all_checkpoints_passed and self.course.check_goal(state["position"]):
            return True

        # 壁衝突（LiDARの最小距離が非常に小さい）
        min_distance = np.min(lidar_scan)
        if min_distance < 0.1:  # 10cm以内で衝突とみなす
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

        return {
            "position": state["position"],
            "speed": state["speed"],
            "angle": state["angle"],
            "step_count": self.step_count,
            "total_reward": self.total_reward,
            "checkpoints_passed": len(self.checkpoints_passed),
            "min_distance": np.min(lidar_scan),
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
            if i not in self.checkpoints_passed:
                self.renderer.draw_checkpoint(
                    tuple(cp["position"]), cp.get("radius", 1.0)
                )

        # ゴールを描画
        goal_pos, goal_radius = self.course.get_goal_info()
        self.renderer.draw_goal(goal_pos, goal_radius)

        # LiDARを描画（キャッシュを使用）
        self.renderer.draw_lidar(
            state["position"], state["angle"], lidar_scan, num_rays=72
        )

        # 車両を描画
        self.renderer.draw_vehicle(self.vehicle)

        # デバッグ情報
        info = self._get_info()
        debug_info = {
            "Speed": info["speed"],
            "Step": info["step_count"],
            "Reward": info["total_reward"],
            "CPs": f"{info['checkpoints_passed']}/{len(checkpoints)}",
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
