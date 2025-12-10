# プロジェクト構造設計

## ディレクトリ構造

```
2d-simulator/
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
│
├── doc/
│   ├── plan/              # 実装計画
│   ├── design/            # 設計ドキュメント
│   └── api/               # APIドキュメント
│
├── src/
│   ├── __init__.py
│   │
│   ├── env/               # シミュレーション環境
│   │   ├── __init__.py
│   │   ├── minicar_env.py          # メインの環境クラス (Gym互換)
│   │   ├── world.py                # 物理世界の管理
│   │   ├── vehicle.py              # 車両モデル
│   │   ├── sensors.py              # センサーシミュレーション
│   │   ├── course.py               # コース定義とロード
│   │   └── renderer.py             # 可視化レンダラー
│   │
│   ├── physics/           # 物理演算
│   │   ├── __init__.py
│   │   ├── box2d_wrapper.py        # Box2Dラッパー
│   │   └── collision_handler.py    # 衝突検出
│   │
│   ├── rl/                # 強化学習関連
│   │   ├── __init__.py
│   │   ├── ppo.py                  # PPOアルゴリズム実装
│   │   ├── policy.py               # ポリシーネットワーク
│   │   ├── value.py                # 価値関数ネットワーク
│   │   ├── buffer.py               # 経験バッファ
│   │   └── trainer.py              # 学習ループ
│   │
│   ├── curriculum/        # カリキュラム学習
│   │   ├── __init__.py
│   │   ├── curriculum_manager.py   # 難易度調整
│   │   └── reward_shaping.py       # 報酬の形成
│   │
│   ├── domain_randomization/  # Domain Randomization
│   │   ├── __init__.py
│   │   ├── physics_randomizer.py   # 物理パラメータのランダム化
│   │   └── sensor_noise.py         # センサーノイズ
│   │
│   ├── utils/             # ユーティリティ
│   │   ├── __init__.py
│   │   ├── config.py               # 設定管理
│   │   ├── logger.py               # ロギング
│   │   └── visualization.py        # データ可視化
│   │
│   └── deploy/            # 実機デプロイ用
│       ├── __init__.py
│       ├── model_converter.py      # モデル変換
│       └── rpi_inference.py        # Raspberry Pi推論
│
├── courses/               # コースデータ
│   ├── easy/
│   │   └── simple_oval.json
│   ├── medium/
│   │   └── shortcut_1.json
│   └── hard/
│       └── narrow_passage.json
│
├── configs/               # 設定ファイル
│   ├── env_config.yaml            # 環境設定
│   ├── training_config.yaml       # 学習設定
│   └── model_config.yaml          # モデル設定
│
├── scripts/               # 実行スクリプト
│   ├── train.py                   # 学習実行
│   ├── evaluate.py                # 評価
│   ├── visualize.py               # 可視化
│   └── create_course.py           # コース作成ツール
│
├── tests/                 # テストコード
│   ├── test_env.py
│   ├── test_vehicle.py
│   ├── test_sensors.py
│   └── test_ppo.py
│
├── notebooks/             # Jupyter Notebooks
│   ├── explore_env.ipynb
│   ├── analyze_training.ipynb
│   └── visualize_policy.ipynb
│
├── models/                # 学習済みモデル
│   ├── checkpoints/
│   └── best/
│
└── logs/                  # ログとTensorBoard
    ├── tensorboard/
    └── training/
```

## 各ディレクトリの役割

### src/env/
シミュレーション環境の中核。Gym互換インターフェースを実装し、物理演算、センサー、レンダリングを統合する。

### src/physics/
Box2Dをラップし、車両の動力学と衝突検出を実装。物理パラメータの調整が容易な設計。

### src/rl/
PPOアルゴリズムの実装。PyTorchを使用し、学習ループ、ポリシー、価値関数を含む。

### src/curriculum/
段階的な学習を管理。コースの難易度調整と報酬の形成を担当。

### src/domain_randomization/
Sim-to-Real対策。物理パラメータとセンサーノイズのランダム化を実装。

### courses/
コース定義をJSONで保存。壁の座標、チェックポイント、スタート/ゴール位置を含む。

### configs/
YAML形式の設定ファイル。ハイパーパラメータを外部から変更可能。

### scripts/
学習、評価、可視化の実行スクリプト。コマンドライン引数で柔軟に実行可能。

### tests/
ユニットテストと統合テスト。CI/CDパイプラインで自動実行。

## モジュール間の依存関係

```
scripts/
  ↓
src/rl/ → src/env/ → src/physics/
  ↓          ↓
src/curriculum/  src/domain_randomization/
  ↓          ↓
src/utils/
```

## 命名規則

- **クラス名**: PascalCase (例: `MinicarEnv`, `PPOTrainer`)
- **関数/メソッド名**: snake_case (例: `step()`, `get_observation()`)
- **定数**: UPPER_SNAKE_CASE (例: `MAX_STEPS`, `LIDAR_RANGE`)
- **プライベートメソッド**: `_`プレフィックス (例: `_compute_reward()`)
- **ファイル名**: snake_case (例: `minicar_env.py`)

## インターフェース設計原則

1. **Gym互換性**: 環境は`gym.Env`を継承し、標準的な`reset()`, `step()`, `render()`を実装
2. **設定の外部化**: ハードコーディングを避け、YAMLファイルで設定管理
3. **疎結合**: 各モジュールは独立して動作可能
4. **テスタビリティ**: 各コンポーネントは単体テストが可能
5. **拡張性**: 新しいセンサーやアルゴリズムを容易に追加可能
