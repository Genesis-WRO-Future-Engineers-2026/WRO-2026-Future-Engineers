# Scripts - 実行スクリプト集

このディレクトリには、2Dシミュレーターを操作・学習・評価するためのスクリプトが含まれています。

---

## 📂 ディレクトリ構成

```
scripts/
├── README.md                    # このファイル
├── simulator-demo/              # デモスクリプト
│   ├── README.md                # デモの詳細説明
│   ├── manual_control.py        # 手動制御デモ
│   └── run_manual_control.sh    # 手動制御の起動スクリプト
├── train.py                     # PPO学習スクリプト
├── test_rl.py                   # RLモジュールの動作確認
└── test_saved_model.py          # 保存モデルのテスト
```

---

## 🎮 デモスクリプト

### 手動制御デモ

シミュレーターをキーボードで手動操作できます。

```bash
# 実行方法1: Pythonスクリプト直接実行
python scripts/simulator-demo/manual_control.py

# 実行方法2: シェルスクリプト実行
./scripts/simulator-demo/run_manual_control.sh

# 実行方法3: scriptsディレクトリから
cd scripts/simulator-demo
./run_manual_control.sh
```

**操作方法:**
- `↑` / `W`: アクセル
- `↓` / `S`: ブレーキ
- `←` / `A`: 左旋回
- `→` / `D`: 右旋回
- `R`: リセット
- `ESC` / `Q`: 終了

詳細は [simulator-demo/README.md](./simulator-demo/README.md) を参照してください。

---

## 🤖 強化学習スクリプト

### 1. 学習スクリプト (`train.py`)

PPOアルゴリズムでエージェントを学習させます。

#### 基本的な使い方

```bash
# デフォルト設定で学習開始
python scripts/train.py

# カスタム設定で学習
python scripts/train.py \
  --total-iterations 1000 \
  --n-steps 2048 \
  --lr 3e-4 \
  --experiment-name my_experiment

# チェックポイントから再開
python scripts/train.py \
  --resume models/checkpoints/checkpoint_500.pth \
  --total-iterations 2000
```

#### 主要なオプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--course` | コースファイル | `courses/easy/simple_oval.json` |
| `--total-iterations` | 総イテレーション数 | 1000 |
| `--n-steps` | 1イテレーションのステップ数 | 2048 |
| `--n-epochs` | 1更新のエポック数 | 10 |
| `--batch-size` | バッチサイズ | 64 |
| `--lr` | 学習率 | 3e-4 |
| `--gamma` | 割引率 | 0.99 |
| `--gae-lambda` | GAEのλ | 0.95 |
| `--clip-range` | PPOクリッピング範囲 | 0.2 |
| `--entropy-coef` | エントロピー係数 | 0.01 |
| `--value-coef` | 価値関数係数 | 0.5 |
| `--save-freq` | 保存頻度（イテレーション） | 50 |
| `--eval-freq` | 評価頻度（イテレーション） | 50 |
| `--device` | デバイス（cpu/cuda/mps/auto） | auto |
| `--experiment-name` | 実験名 | 自動生成 |

#### 使用例

```bash
# 短時間のテスト実行（約5分）
python scripts/train.py \
  --total-iterations 10 \
  --n-steps 512 \
  --experiment-name quick_test

# 本格的な学習（約2-3時間）
python scripts/train.py \
  --total-iterations 1000 \
  --n-steps 2048 \
  --save-freq 100 \
  --experiment-name full_training

# Apple Silicon (MPS) で高速学習
python scripts/train.py \
  --device mps \
  --total-iterations 500
```

#### 学習の進捗確認

**TensorBoardで可視化:**
```bash
# 別ターミナルで実行
tensorboard --logdir=logs

# ブラウザで http://localhost:6006 を開く
```

**CSVログの確認:**
```bash
# 学習ログを表示
cat logs/<experiment_name>/training.csv | column -t -s,
```

---

### 2. RLモジュールテスト (`test_rl.py`)

強化学習モジュールの動作確認を行います。

```bash
python scripts/test_rl.py
```

**テスト内容:**
- ✓ ポリシーネットワークのテスト
- ✓ 価値関数ネットワークのテスト
- ✓ ロールアウトバッファのテスト
- ✓ PPOアルゴリズムのテスト
- ✓ 環境との統合テスト

**実行時間:** 約10-20秒

**用途:**
- 新規実装の動作確認
- 環境セットアップ後の検証
- バグ修正後のサニティチェック

---

### 3. 保存モデルテスト (`test_saved_model.py`)

学習済みモデルを読み込んで評価します。

```bash
# デフォルト（final_model.pth）を3エピソード評価
python scripts/test_saved_model.py

# 特定のチェックポイントを評価
python scripts/test_saved_model.py \
  --model models/checkpoints/checkpoint_500.pth \
  --n-episodes 5

# ベストモデルを評価
python scripts/test_saved_model.py \
  --model models/best/policy.pth \
  --n-episodes 10
```

**オプション:**
| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--model` | モデルファイルのパス | `models/checkpoints/final_model.pth` |
| `--n-episodes` | 評価エピソード数 | 3 |

**出力例:**
```
Episode 1:
  Reward: 245.32
  Length: 856
  Checkpoints: 4
  Final position: (2.15, 5.03)
  Final speed: 1.25 m/s

Summary:
Average Reward: 238.45 ± 12.34
Average Length: 872.3 ± 45.6
Average Checkpoints: 3.7 ± 0.5
```

---

## 📊 学習ワークフロー例

### 1. 初めての学習

```bash
# 1. 短時間テスト実行（動作確認）
python scripts/train.py \
  --total-iterations 5 \
  --n-steps 256 \
  --experiment-name initial_test

# 2. テスト結果を確認
python scripts/test_saved_model.py

# 3. TensorBoardで可視化
tensorboard --logdir=logs

# 4. 問題なければ本格的な学習を開始
python scripts/train.py \
  --total-iterations 1000 \
  --experiment-name main_training
```

### 2. 学習の継続

```bash
# チェックポイントから再開
python scripts/train.py \
  --resume models/checkpoints/checkpoint_500.pth \
  --total-iterations 1500 \
  --experiment-name continued_training
```

### 3. ハイパーパラメータ調整

```bash
# 学習率を変更
python scripts/train.py \
  --lr 1e-4 \
  --experiment-name lr_1e4

# クリッピング範囲を変更
python scripts/train.py \
  --clip-range 0.1 \
  --experiment-name clip_01

# エントロピー係数を変更（探索を促進）
python scripts/train.py \
  --entropy-coef 0.05 \
  --experiment-name entropy_005
```

---

## 🔍 トラブルシューティング

### 学習が進まない場合

1. **報酬関数を確認:**
   ```bash
   # 手動制御で報酬を確認
   python scripts/simulator-demo/manual_control.py
   ```

2. **学習率を調整:**
   ```bash
   python scripts/train.py --lr 1e-4  # 学習率を下げる
   ```

3. **ステップ数を増やす:**
   ```bash
   python scripts/train.py --n-steps 4096
   ```

### メモリ不足の場合

```bash
# バッチサイズを減らす
python scripts/train.py --batch-size 32

# ステップ数を減らす
python scripts/train.py --n-steps 1024
```

### GPU/MPSが使えない場合

```bash
# CPUを強制
python scripts/train.py --device cpu
```

---

## 📁 出力ファイル

### 学習中に生成されるファイル

```
models/checkpoints/
├── checkpoint_50.pth         # 50イテレーション時点
├── checkpoint_100.pth        # 100イテレーション時点
├── checkpoint_150.pth        # 150イテレーション時点
└── final_model.pth           # 最終モデル

logs/<experiment_name>/
├── hyperparameters.json      # ハイパーパラメータ
├── training.csv              # 学習ログ（CSV形式）
└── events.out.tfevents.*     # TensorBoardログ
```

### ファイルサイズの目安

- チェックポイント: 約2.0MB/ファイル
- TensorBoardログ: 約10-50MB（学習時間による）
- CSVログ: 約1-5KB

---

## 🚀 次のステップ

1. **デモで環境を確認:**
   ```bash
   python scripts/simulator-demo/manual_control.py
   ```

2. **テスト実行:**
   ```bash
   python scripts/test_rl.py
   ```

3. **短時間学習:**
   ```bash
   python scripts/train.py --total-iterations 10
   ```

4. **結果確認:**
   ```bash
   python scripts/test_saved_model.py
   tensorboard --logdir=logs
   ```

5. **本格的な学習:**
   ```bash
   python scripts/train.py --total-iterations 1000
   ```

---

## 📚 関連ドキュメント

- [プロジェクトREADME](../README.md)
- [実装計画](../doc/plan/init/README.md)
- [設定ファイル](../configs/ppo_default.yaml)
- [Phase 2完了レポート](../doc/phase2_completion.md)（予定）

---

## ⚡ クイックリファレンス

```bash
# 手動制御
python scripts/simulator-demo/manual_control.py

# テスト実行
python scripts/test_rl.py

# 短時間学習
python scripts/train.py --total-iterations 10

# 本格学習
python scripts/train.py --total-iterations 1000

# モデル評価
python scripts/test_saved_model.py

# TensorBoard
tensorboard --logdir=logs
```

---

**作成日**: 2025-12-10
**バージョン**: 1.0.0
