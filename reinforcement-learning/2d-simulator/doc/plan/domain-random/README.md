# Domain Randomization実装計画

## 📋 目次

このディレクトリには、Domain Randomization機能の詳細な実装計画が含まれています。

### ドキュメント一覧

- **[00_overview.md](./00_overview.md)** - 概要と目的
- **[01_implementation_details.md](./01_implementation_details.md)** - 実装詳細とコード設計
- **[02_integration_guide.md](./02_integration_guide.md)** - 既存コードへの統合手順
- **[03_testing_strategy.md](./03_testing_strategy.md)** - テスト戦略と検証方法

## 🎯 実装の目的

Domain Randomizationを導入することで、シミュレーターで学習したポリシーを実機に転移する際のギャップ（Sim2Real Gap）を軽減します。

### 主要な効果

1. **ロバスト性の向上**: 物理パラメータの変動に強いポリシー
2. **センサーノイズ耐性**: LiDARの測定誤差に対応
3. **環境変動への適応**: 床面の摩擦変化、モーター性能のばらつきに対応
4. **実機転移の成功率向上**: シミュレーションと実機の差を吸収

## 📊 現状分析

### ✅ 既に実装されている機能

1. **センサーノイズ関数** (`src/env/sensors.py`)
   - `add_noise()`: 基本ガウシアンノイズ
   - `add_advanced_noise()`: ドロップアウト + スパイクノイズ
   - **問題**: 学習ループで使用されていない

2. **コースバリエーション** (`scripts/course-generation/create_course_variations.py`)
   - 壁位置のランダム化（±5cm）
   - 5つのバリエーション生成済み

### ❌ 未実装の機能

1. **物理パラメータのランダム化**
   - 摩擦係数、質量、慣性
   - モーター応答遅延、トルク変動

2. **専用モジュール**
   - `src/domain_randomization/physics_randomizer.py`
   - `src/domain_randomization/sensor_noise.py`

3. **学習への統合**
   - 環境初期化時のランダム化
   - エピソードごとのパラメータ更新

## ⏱️ 実装スケジュール

### 総期間: 5-7日

- **Day 1-2**: PhysicsRandomizerの実装
- **Day 3**: SensorNoiseの統合
- **Day 4-5**: MinicarEnvへの統合とテスト
- **Day 6**: 学習スクリプトの更新
- **Day 7**: ドキュメント整備と最終検証

## 🚀 実装の優先順位

### Phase 1: 基本実装（必須）

1. **PhysicsRandomizer** - 物理パラメータのランダム化
2. **SensorNoise** - センサーノイズの統合
3. **MinicarEnv統合** - 環境への組み込み

### Phase 2: 学習統合（必須）

4. **学習スクリプト更新** - コマンドライン引数の追加
5. **動作検証** - Domain Randomizationありでの学習テスト

### Phase 3: 最適化（推奨）

6. **パラメータチューニング** - ノイズレベルの調整
7. **実機検証** - 実機での転移性能確認

## 📖 推奨読み順

### 初めての方

1. **00_overview.md** - 全体像を理解
2. **01_implementation_details.md** - 実装の詳細を確認
3. **02_integration_guide.md** - 統合手順を確認

### 実装を進める方

1. **01_implementation_details.md** - コード設計を確認
2. **02_integration_guide.md** - ステップバイステップで実装
3. **03_testing_strategy.md** - テスト実施

## 🎓 関連ドキュメント

- **元の実装計画**: `doc/plan/init/03_implementation_phases.md` (Week 7)
- **Sim2Real戦略**: `doc/plan/init/06_sim_to_real.md`
- **プロジェクト概要**: `doc/plan/init/00_overview.md`

## 📝 バージョン

- **作成日**: 2025-12-12
- **バージョン**: 1.0.0
- **対象プロジェクト**: 2D Minicar Simulator v1.0

## 🔄 更新履歴

- 2025-12-12: 初版作成
