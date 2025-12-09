# 2Dシミュレーター実装計画 - 目次

このディレクトリには、ミニカー自動運転のための2D強化学習シミュレーターの詳細な実装計画が含まれています。

## ドキュメント一覧

### [00_overview.md](./00_overview.md) - 概要
- プロジェクトの目的と全体像
- 実装フェーズの概要
- 期待される成果物
- 成功指標

### [01_project_structure.md](./01_project_structure.md) - プロジェクト構造
- ディレクトリ構造の詳細
- 各モジュールの役割
- モジュール間の依存関係
- 命名規則とインターフェース設計原則

### [02_tech_stack.md](./02_tech_stack.md) - 技術スタック
- 使用するライブラリとその選定理由
- 完全なrequirements.txt
- 開発ツールの推奨事項
- ハードウェア要件

### [03_implementation_phases.md](./03_implementation_phases.md) - 実装フェーズ
- Phase 1: 基盤構築（2-3週間）
- Phase 2: 強化学習統合（2-3週間）
- Phase 3: 高度な機能（2-3週間）
- Phase 4: 検証と最適化（1-2週間）
- 各フェーズの詳細タスクとマイルストーン

### [04_component_design.md](./04_component_design.md) - コンポーネント設計
- シミュレーション環境の詳細設計
- 物理エンジンの実装
- 強化学習アルゴリズム（PPO）
- カリキュラム学習とDomain Randomization
- 実装例とコードスニペット

### [05_config_and_testing.md](./05_config_and_testing.md) - 設定とテスト
- 設定ファイルのサンプル（YAML形式）
- ユニットテスト戦略
- 統合テストとパフォーマンステスト
- CI/CD設定
- デバッグとトラブルシューティング

### [06_sim_to_real.md](./06_sim_to_real.md) - 実機転移
- Domain Randomization戦略
- 実機セットアップ手順
- モデルのデプロイ（PyTorch → ONNX）
- センサー・モーターキャリブレーション
- 段階的な転移プロセス
- トラブルシューティングと安全対策

### [07_getting_started.md](./07_getting_started.md) - 実装開始ガイド
- 開発環境のセットアップ手順
- Phase 1の具体的な実装順序
- 各タスクの実装例とテストコード
- 開発ワークフローとデバッグのヒント

---

## 推奨読み順

### 初めての方
1. **00_overview.md** - プロジェクト全体を理解
2. **01_project_structure.md** - 構造を把握
3. **07_getting_started.md** - 実装を開始

### 設計を理解したい方
1. **02_tech_stack.md** - 技術選定の背景
2. **04_component_design.md** - 詳細設計
3. **05_config_and_testing.md** - テスト戦略

### 実装を進める方
1. **03_implementation_phases.md** - タスクリスト
2. **07_getting_started.md** - 実装ガイド
3. **05_config_and_testing.md** - テスト実装

### 実機転移を考える方
1. **06_sim_to_real.md** - 転移戦略
2. **04_component_design.md** - ポリシーのデプロイ
3. **05_config_and_testing.md** - 実機テスト

---

## クイックリファレンス

### プロジェクト期間
- **総期間**: 8-10週間
- **Phase 1**: 2-3週間（基盤構築）
- **Phase 2**: 2-3週間（強化学習）
- **Phase 3**: 2-3週間（高度な機能）
- **Phase 4**: 1-2週間（検証）

### 主要技術
- **物理エンジン**: Box2D (PyBox2D)
- **強化学習**: PyTorch + PPO（スクラッチ実装）
- **環境**: Gymnasium
- **可視化**: Pygame, Matplotlib, TensorBoard

### 主要コンポーネント
1. **MinicarEnv** - Gym互換環境
2. **Vehicle** - 車両モデル
3. **LiDARSensor** - センサーシミュレーション
4. **Course** - コース定義
5. **PPO** - 強化学習アルゴリズム
6. **CurriculumManager** - カリキュラム学習
7. **PhysicsRandomizer** - Domain Randomization

---

## 重要なマイルストーン

### Phase 1完了条件
- [ ] 手動制御でコースを走行可能
- [ ] LiDARスキャンが正確に機能
- [ ] Pygameで可視化できる
- [ ] Gym互換インターフェースが動作

### Phase 2完了条件
- [ ] シンプルなコースで完走可能（成功率50%以上）
- [ ] PPOアルゴリズムが収束
- [ ] TensorBoardで学習過程を確認可能

### Phase 3完了条件
- [ ] カリキュラム学習が機能
- [ ] Domain Randomizationで学習が収束
- [ ] ショートカットを活用して走行

### Phase 4完了条件
- [ ] 評価指標が目標値を達成
- [ ] 実機デプロイ用コードが動作
- [ ] ドキュメントが整備されている

---

## 連絡先・質問

実装中に疑問が生じた場合:
1. 関連するドキュメントを再確認
2. テストコードを参考に実装
3. デバッグセクションを確認

---

## バージョン

- **作成日**: 2025-12-09
- **バージョン**: 1.0.0
- **最終更新**: 2025-12-09

---

## ライセンス

このプロジェクトは社内プロジェクトです。

---

## 次のアクション

1. **開発環境のセットアップ**: [07_getting_started.md](./07_getting_started.md)を参照
2. **Phase 1の開始**: [03_implementation_phases.md](./03_implementation_phases.md)のWeek 1タスクを確認
3. **最初のコミット**: ディレクトリ構造とrequirements.txtを作成

それでは、実装を開始しましょう！
