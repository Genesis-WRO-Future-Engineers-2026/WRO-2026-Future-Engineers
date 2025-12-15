"""Domain Randomization設定のプリセット"""

from .physics_randomizer import PhysicsRandomizationConfig
from .sensor_noise import SensorNoiseConfig


# レベル1: 無効化（デフォルト）
DISABLED_CONFIG = {
    'physics': None,
    'sensor': None,
}

# レベル2: 軽微なランダム化（最初のテスト用）
MILD_CONFIG = {
    'physics': PhysicsRandomizationConfig(
        friction_range=(0.6, 0.8),
        mass_range=(1.3, 1.5),
        inertia_scale_range=(0.9, 1.1),
        motor_force_range=(19.0, 21.0),
        motor_delay_range=(0.0, 0.02),
        linear_damping_range=(0.45, 0.55),
        angular_damping_range=(0.7, 0.9),
        max_lateral_impulse_range=(2.3, 2.7),
    ),
    'sensor': SensorNoiseConfig(
        noise_level_range=(0.005, 0.01),
        dropout_prob_range=(0.01, 0.02),
        spike_prob_range=(0.002, 0.005),
    ),
}

# レベル3: 標準ランダム化（通常の学習用）
STANDARD_CONFIG = {
    'physics': PhysicsRandomizationConfig(
        friction_range=(0.5, 0.9),
        mass_range=(1.2, 1.6),
        inertia_scale_range=(0.85, 1.15),
        motor_force_range=(18.5, 21.5),
        motor_delay_range=(0.0, 0.03),
        linear_damping_range=(0.4, 0.6),
        angular_damping_range=(0.65, 0.95),
        max_lateral_impulse_range=(2.2, 2.8),
    ),
    'sensor': SensorNoiseConfig(
        noise_level_range=(0.01, 0.015),
        dropout_prob_range=(0.02, 0.04),
        spike_prob_range=(0.005, 0.008),
    ),
}

# レベル4: 強めのランダム化（実機転移用）
STRONG_CONFIG = {
    'physics': PhysicsRandomizationConfig(
        friction_range=(0.5, 1.0),
        mass_range=(1.2, 1.6),
        inertia_scale_range=(0.8, 1.2),
        motor_force_range=(18.0, 22.0),
        motor_delay_range=(0.0, 0.05),
        linear_damping_range=(0.4, 0.6),
        angular_damping_range=(0.6, 1.0),
        max_lateral_impulse_range=(2.0, 3.0),
    ),
    'sensor': SensorNoiseConfig(
        noise_level_range=(0.01, 0.02),
        dropout_prob_range=(0.02, 0.05),
        spike_prob_range=(0.005, 0.01),
    ),
}


def get_config(level: str = 'disabled'):
    """設定レベルに応じたConfigを取得

    Args:
        level: 'disabled', 'mild', 'standard', 'strong'

    Returns:
        {'physics': PhysicsRandomizationConfig, 'sensor': SensorNoiseConfig}
    """
    configs = {
        'disabled': DISABLED_CONFIG,
        'mild': MILD_CONFIG,
        'standard': STANDARD_CONFIG,
        'strong': STRONG_CONFIG,
    }

    if level not in configs:
        raise ValueError(f"Unknown config level: {level}. Choose from {list(configs.keys())}")

    return configs[level]
