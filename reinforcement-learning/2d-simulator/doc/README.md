# ドキュメント

このディレクトリには、2Dシミュレータープロジェクトの主要ドキュメントが含まれています。

## 主要ドキュメント

### 学習システム
- **[ADAPTIVE_TRAINING.md](ADAPTIVE_TRAINING.md)** - 適応的学習システムの詳細
  - カリキュラム学習（Level 0-5）
  - 適応的報酬スケーリング（3フェーズ）
  - 使い方とトラブルシューティング

### 報酬設計
- **[REWARD_DESIGN.md](REWARD_DESIGN.md)** - 報酬関数の設計思想
  - 報酬関数の構成と履歴（v1.0 → v3.2）
  - 各項目の詳細説明
  - Sim2Real転移の考慮事項

### 車両仕様
- **[vehicle-specifications.md](vehicle-specifications.md)** - TT-02実機スペック
  - 物理パラメータ
  - センサー仕様

## アーカイブ

過去の計画文書・完了報告は`archive/`ディレクトリに保存されています:

```
archive/
├── PHASE1_COMPLETE.md           # Phase 1完了報告
└── plan/                        # 過去の計画文書
    ├── init/                    # 初期計画（Phase 1）
    ├── domain-random/           # Domain Randomization計画
    ├── real-course/             # 実コース設計
    ├── refactor/                # リファクタリング計画・報告
    └── tmp/                     # 一時的な分析レポート
```

これらは参考用に保持されていますが、現在の開発には直接関係ありません。

## ディレクトリ構成

```
doc/
├── README.md                    # このファイル
├── ADAPTIVE_TRAINING.md         # 適応的学習システム（メイン）
├── REWARD_DESIGN.md             # 報酬設計
├── vehicle-specifications.md    # 車両仕様
└── archive/                     # アーカイブ（過去の文書）
```

## 関連ドキュメント

プロジェクト全体のドキュメント:
- **[トップレベルREADME](../README.md)** - プロジェクト全体の概要とクイックスタート
- **[コース定義](../courses/curriculum/)** - Level 0-5のコース定義（JSON）

## 更新履歴

- **2025-12-15**: ドキュメント整理
  - すべての説明文書を`doc/`に統合
  - `courses/curriculum/README.md`を`ADAPTIVE_TRAINING.md`に統合
  - `doc/rl-training/`を`doc/`直下に移動
  - 古い計画文書を`archive/`に移動
  - このREADME.mdを作成
