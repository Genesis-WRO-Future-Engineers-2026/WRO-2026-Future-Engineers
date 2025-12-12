# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

2Dシミュレーター環境でミニカーの自動運転をPPO強化学習で実現するプロジェクト。Box2D物理エンジン、72方向LiDARセンサー、Gymnasium互換環境を使用。

## Environment Setup

**重要**: すべてのコマンド実行前に以下を実行:

```bash
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

PYTHONPATHの設定を忘れると`ModuleNotFoundError: No module named 'src'`が発生する。

## Common Commands

### Training

```bash
# 基本的な学習（GUI付き）
python scripts/rl-training/train.py --total-iterations 100 --gui

# GUIなし高速学習
python scripts/rl-training/train.py --total-iterations 1000

# チェックポイントから再開
python scripts/rl-training/train.py --resume models/checkpoints/checkpoint_50.pth --total-iterations 2000

# カリキュラム学習
python scripts/rl-training/train_curriculum.py
```

### Testing

```bash
# すべてのテスト実行
pytest tests/

# 特定のテスト実行
pytest tests/test_env.py -v

# カバレッジ付き
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# フォーマット
black src/ tests/

# Linter
flake8 src/ tests/
```

### Evaluation

```bash
# 学習済みモデルを可視化
python scripts/rl-training/test_saved_model.py --model models/checkpoints/final_model.pth

# TensorBoard起動
tensorboard --logdir=logs
```

## Architecture

### 3層アーキテクチャ

1. **物理層** (`src/physics/`): Box2D物理エンジンのラッパー
2. **環境層** (`src/env/`): Gymnasium互換のRL環境
3. **学習層** (`src/rl/`): PPOアルゴリズムと学習ループ

### データフロー

```
Course (JSON) → PhysicsWorld (Box2D) → Vehicle → LiDARSensor
                                          ↓
                                     MinicarEnv (Gym)
                                          ↓
                                     PPO → Trainer
```

### 観測空間構成 (10次元)

- LiDAR: 5次元（前方120度を5方向でカバー: -60° ~ +60°）
- 速度: 2次元（vx, vy）
- 角速度: 1次元
- 前回の行動: 2次元（steering, throttle）

**Sim2Real対応**:
- チェックポイント情報は観測空間に含めない
- 学習時はチェックポイントを報酬計算に使用（進捗管理・学習補助）
- エージェントはLiDARと速度情報のみで走行を学習
- 本番環境（6分間連続周回レース）でも同じ10次元観測空間を使用

### 行動空間 (2次元連続)

- steering: [-1.0, 1.0] (左/右)
- throttle: [-1.0, 1.0] (後退/前進)

### 報酬設計

`src/env/minicar_env.py`の`_compute_reward()`メソッドで実装:

- 速度報酬: `speed * 0.03` (チェックポイント情報なしに対応し抑制)
- 時間ペナルティ: `-0.2` (探索時間を許容するため緩和)
- 壁接近ペナルティ: `min_distance < 0.3`で発動
- 衝突ペナルティ: `-100.0` (Box2D物理衝突検出)
- チェックポイント報酬: `+200.0` (偶然の通過を強く評価)
- ゴール到達報酬: `+500.0`
- 時間ボーナス: `(max_steps - current_step) * 1.5` (早くゴールするほど高い)

**10次元観測空間に対応した報酬設計**:
- エージェントはチェックポイントの方向を観測できない
- チェックポイント報酬を強化し、偶然の通過から学習を促進
- 速度報酬を抑制し、闇雲な走行を防ぐ
- 時間ペナルティを緩和し、探索時間を許容

報酬関数を変更する場合はこのメソッドを編集。

### 衝突判定

Box2Dの物理エンジンによる衝突検出を使用（`src/physics/collision_listener.py`）:

- **全方向・全角度の正確な衝突検出**（前後左右すべて）
- LiDARは観測空間として使用（前方120度のみ）
- 衝突時はエピソードが即座に終了

### PPOパラメータ

デフォルト値（`src/rl/ppo.py`）:

- learning_rate: 3e-4
- gamma: 0.99
- gae_lambda: 0.95
- clip_range: 0.2
- entropy_coef: 0.01
- n_steps: 2048
- n_epochs: 10
- batch_size: 64

### カリキュラム学習

`src/curriculum/curriculum_manager.py`で実装。成功率ベースで難易度を自動調整:

- success_threshold: 0.8 (レベルアップ閾値)
- degradation_threshold: 0.3 (レベルダウン閾値)
- evaluation_window: 100エピソード

新しいコースは`courses/`ディレクトリにJSON形式で追加。

## コース定義

`courses/`以下にJSON形式で定義:

```json
{
  "name": "コース名",
  "start_position": [x, y],
  "start_angle": 0.0,
  "goal_position": [x, y],
  "goal_radius": 0.5,
  "walls": [
    {
      "type": "polygon",
      "vertices": [[x1, y1], [x2, y2], ...]
    }
  ],
  "checkpoints": [
    {
      "position": [x, y],
      "radius": 1.0,
      "index": 0
    }
  ]
}
```

## キャッシング戦略

`MinicarEnv`はパフォーマンス最適化のため、LiDARスキャンと車両状態をキャッシュ:

```python
self._cached_lidar_scan = None
self._cached_vehicle_state = None
```

`step()`メソッド内で1回だけ計算し、`_get_observation()`, `_compute_reward()`, `_check_terminated()`, `_get_info()`で再利用。

新しい観測や報酬計算を追加する際はこのキャッシュ機構を活用すること。

## GUI可視化

`--gui`フラグで有効化。Pygameによるリアルタイム描画:

- 車両、壁、LiDAR、チェックポイント、ゴールを描画
- カメラは車両を自動追従
- デバッグ情報（速度、ステップ、報酬）を表示

描画処理は`src/env/renderer.py`で実装。

## チェックポイント管理

モデルは`models/checkpoints/`に保存:

- `checkpoint_N.pth`: N回目のイテレーション
- `final_model.pth`: 学習完了時の最終モデル

PyTorch形式で保存され、policy, value_net, optimizerの状態を含む。

## 未実装コンポーネント

- `src/domain_randomization/`: Domain Randomization（実機転移用）
- `src/deploy/`: 実機デプロイ（ONNX変換、Raspberry Pi推論）

これらは将来の実装予定。

## トラブルシューティング

### ModuleNotFoundError
→ `export PYTHONPATH="$(pwd):$PYTHONPATH"`を実行

### Pygameウィンドウが開かない
→ ローカル環境で実行（GUIはDockerでは動作しない）

### Box2Dインストールエラー
→ macOS: `brew install swig`、Linux: `sudo apt-get install swig`

### 学習が進まない
→ 報酬関数をデバッグ（`info['total_reward']`を確認）
→ ハイパーパラメータ調整（特にlearning_rate, entropy_coef）

## 日本語対応

コードベース、コメント、ドキュメントは日本語で記述されている。新しいコードを追加する際も日本語コメントを使用すること。
