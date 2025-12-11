# チェックポイント順序通過機能 実装計画

## 概要

チェックポイントを順番に通過しないと報酬が得られない仕組みを実装する。

## 現状の問題

### 現在の実装 (`src/env/minicar_env.py:229-235`)

```python
# 4. チェックポイント報酬
checkpoints = self.course.get_checkpoints()
for i, checkpoint in enumerate(checkpoints):
    if i not in self.checkpoints_passed:
        if self.course.check_checkpoint(state["position"], i):
            self.checkpoints_passed.add(i)
            reward += 50.0
```

**問題点:**
- `self.checkpoints_passed = set()` - 順序情報がない
- 全チェックポイントをループで判定 → どの順番でも通過可能
- チェックポイント0→1→2→3でも、3→2→1→0でも報酬が得られる

**具体例:**
```
コース: start(1,1) → CP0(5,1.5) → CP1(9,5) → CP2(5,8.5) → CP3(1,5) → goal(1,1)

現在の実装では以下が可能:
- start → CP3(近い) → CP0 → CP1 → CP2 → goal ✅ (ショートカット)
- start → CP2 → CP3 → CP0 → CP1 → goal ✅ (逆走)
```

---

## 実装方針

### 設計原則

1. **順序厳守**: チェックポイントはインデックス順（0→1→2→...）にのみ通過可能
2. **次のチェックポイントのみ判定**: 現在の次のチェックポイントだけを監視
3. **後方互換性**: 既存のコースJSON形式を変更しない
4. **デバッグ可能**: どのチェックポイントが次か、ログで確認可能

---

## 詳細設計

### 1. 状態管理の変更

**変更対象:** `src/env/minicar_env.py`

#### 1.1 インスタンス変数の変更

```python
# 変更前
self.checkpoints_passed = set()  # 順序なし

# 変更後
self.next_checkpoint_index = 0  # 次に通過すべきチェックポイントのインデックス
```

**理由:**
- `set()`ではなく整数インデックスで管理
- 次に通過すべきチェックポイントが明確
- メモリ効率的（set → int）

---

### 2. チェックポイント判定ロジックの変更

**変更対象:** `src/env/minicar_env.py:229-235`

#### 2.1 報酬計算の変更

```python
# 変更前
checkpoints = self.course.get_checkpoints()
for i, checkpoint in enumerate(checkpoints):
    if i not in self.checkpoints_passed:
        if self.course.check_checkpoint(state["position"], i):
            self.checkpoints_passed.add(i)
            reward += 50.0

# 変更後
checkpoints = self.course.get_checkpoints()
if self.next_checkpoint_index < len(checkpoints):
    # 次のチェックポイントのみ判定
    if self.course.check_checkpoint(state["position"], self.next_checkpoint_index):
        reward += 50.0
        self.next_checkpoint_index += 1  # 次へ進む
```

**メリット:**
- O(n)ループ → O(1)判定に改善（パフォーマンス向上）
- 順序が強制される
- コードが簡潔

---

### 3. ゴール到達条件の変更

**変更対象:** `src/env/minicar_env.py:237-241`

#### 3.1 報酬計算

```python
# 変更前
if self.course.check_goal(state["position"]):
    if len(self.checkpoints_passed) == len(checkpoints):
        reward += 500.0

# 変更後
if self.course.check_goal(state["position"]):
    # 全チェックポイントを順番に通過済みか確認
    if self.next_checkpoint_index == len(checkpoints):
        reward += 500.0
```

#### 3.2 終了条件 (`_check_terminated()`)

```python
# 変更前 (src/env/minicar_env.py:256-260)
checkpoints = self.course.get_checkpoints()
all_checkpoints_passed = len(self.checkpoints_passed) == len(checkpoints)
if all_checkpoints_passed and self.course.check_goal(state["position"]):
    return True

# 変更後
checkpoints = self.course.get_checkpoints()
all_checkpoints_passed = self.next_checkpoint_index == len(checkpoints)
if all_checkpoints_passed and self.course.check_goal(state["position"]):
    return True
```

---

### 4. リセット時の初期化

**変更対象:** `src/env/minicar_env.py:97-130` (reset()メソッド)

```python
# 変更前
self.checkpoints_passed = set()

# 変更後
self.next_checkpoint_index = 0
```

---

### 5. デバッグ情報の追加

**変更対象:** `src/env/minicar_env.py:270-290` (`_get_info()`メソッド)

```python
# 追加
info = {
    # ... (既存の情報)
    "next_checkpoint_index": self.next_checkpoint_index,
    "total_checkpoints": len(self.course.get_checkpoints()),
    "checkpoints_remaining": len(self.course.get_checkpoints()) - self.next_checkpoint_index,
}
```

**メリット:**
- TensorBoardで進捗を可視化
- デバッグが容易
- 学習の様子を監視可能

---

## 実装手順

### Phase 1: コア機能の実装 (必須)

1. ✅ `minicar_env.py`の`__init__`で変数変更
   - `self.checkpoints_passed` → `self.next_checkpoint_index`

2. ✅ `reset()`メソッドで初期化変更
   - `self.checkpoints_passed = set()` → `self.next_checkpoint_index = 0`

3. ✅ `_compute_reward()`でチェックポイント判定変更
   - ループ → 単一インデックス判定

4. ✅ `_compute_reward()`でゴール報酬条件変更
   - `len(self.checkpoints_passed) == len(checkpoints)` → `self.next_checkpoint_index == len(checkpoints)`

5. ✅ `_check_terminated()`で終了条件変更
   - 同様に`next_checkpoint_index`を使用

### Phase 2: デバッグ情報の追加 (推奨)

6. ✅ `_get_info()`にチェックポイント進捗情報追加

### Phase 3: テスト (必須)

7. ✅ 単体テストで動作確認
   - 順番通りの通過 → 報酬獲得
   - 順番違反 → 報酬なし
   - ゴール到達条件

8. ✅ 学習スクリプトで動作確認
   - 短時間学習（100イテレーション）
   - ログ確認

---

## テストケース

### テスト1: 正常な順序通過

**シナリオ:**
```
start(1,1) → CP0(5,1.5) → CP1(9,5) → CP2(5,8.5) → CP3(1,5) → goal(1,1)
```

**期待結果:**
- CP0通過時: +50報酬、`next_checkpoint_index = 1`
- CP1通過時: +50報酬、`next_checkpoint_index = 2`
- CP2通過時: +50報酬、`next_checkpoint_index = 3`
- CP3通過時: +50報酬、`next_checkpoint_index = 4`
- goal到達時: +500報酬、エピソード終了

**合計報酬:** 50×4 + 500 = 700

---

### テスト2: 順序違反（スキップ）

**シナリオ:**
```
start(1,1) → CP1(9,5) をスキップしてCP0の次にCP2に到達
```

**期待結果:**
- CP0通過時: +50報酬、`next_checkpoint_index = 1`
- CP2到達時: **報酬なし**（CP1がまだ通過していない）
- `next_checkpoint_index = 1`のまま（変化なし）
- その後CP1に戻って通過: +50報酬、`next_checkpoint_index = 2`

---

### テスト3: ショートカット阻止

**シナリオ:**
```
start(1,1) → CP3(近い、1,5) に直行
```

**期待結果:**
- CP3到達時: **報酬なし**（CP0, CP1, CP2を通過していない）
- `next_checkpoint_index = 0`のまま
- ゴール到達不可（全チェックポイント未通過）

---

### テスト4: ゴール到達失敗

**シナリオ:**
```
start → CP0 → CP1 → goal（CP2, CP3をスキップ）
```

**期待結果:**
- ゴール到達時: **+500報酬なし**（`next_checkpoint_index = 2 ≠ 4`）
- エピソード終了しない（`_check_terminated() = False`）
- ゴールエリアに留まるが報酬なし

---

## 後方互換性の確認

### コースJSONフォーマット

**変更なし:**
```json
"checkpoints": [
  {
    "position": [5.0, 1.5],
    "radius": 1.0,
    "index": 0
  },
  ...
]
```

**注意点:**
- `"index"`フィールドは元々存在するが、現在は使用されていない
- 今回の実装では配列の順序（0, 1, 2, ...）を使用
- `"index"`フィールドは将来的に検証用に使用可能

---

## パフォーマンスへの影響

### 改善点

**変更前:**
```python
# O(n) - 全チェックポイントをループ
for i, checkpoint in enumerate(checkpoints):
    if i not in self.checkpoints_passed:  # O(1) set lookup
        if self.course.check_checkpoint(...):  # 距離計算
```
- 時間計算量: O(n) × ステップ数
- チェックポイント数が多いと遅い

**変更後:**
```python
# O(1) - 次のチェックポイントのみ判定
if self.next_checkpoint_index < len(checkpoints):
    if self.course.check_checkpoint(...):  # 距離計算1回
```
- 時間計算量: O(1)
- チェックポイント数に依存しない

**改善率:** チェックポイント4個の場合、最大4倍高速化

---

## リスクと対策

### リスク1: 既存のチェックポイントが破綻

**リスク:**
- 既存コースのチェックポイント配置が順序通りでない可能性

**対策:**
- 全コースファイルをレビュー
- チェックポイント配置の妥当性を確認
- 必要に応じてコース修正

### リスク2: 学習済みモデルの破棄

**リスク:**
- 既存の学習済みモデルは新しいルールに対応していない

**対策:**
- 学習を最初からやり直す（推奨）
- ドキュメントに明記

### リスク3: チェックポイント配置ミス

**リスク:**
- コース設計者が順序を間違えると学習不可能

**対策:**
- コース検証ツールの作成（将来）
- ドキュメントに設計ガイドライン追加

---

## 実装後の確認事項

### 動作確認

- [ ] 単体テスト: 順序通過
- [ ] 単体テスト: 順序違反
- [ ] 単体テスト: ゴール条件
- [ ] GUIで目視確認（`--gui`オプション）
- [ ] 短時間学習で報酬推移確認

### ドキュメント更新

- [ ] `CLAUDE.md`の報酬設計セクション更新
- [ ] コース設計ガイドライン作成
- [ ] 実装計画書の完了報告

---

## 実装優先度

### 必須 (Must Have)
- ✅ Phase 1: コア機能の実装
- ✅ Phase 3: テスト（最低限）

### 推奨 (Should Have)
- ✅ Phase 2: デバッグ情報の追加
- ✅ 全コースファイルのレビュー
- ✅ Phase 3: 完全なテスト

### オプション (Nice to Have)
- コース検証ツール
- チェックポイント配置の自動最適化
- 可視化ツールの改善

---

## タイムライン

| タスク | 所要時間 | 優先度 |
|--------|----------|--------|
| Phase 1実装 | 15分 | 必須 |
| Phase 2実装 | 10分 | 推奨 |
| テスト作成・実行 | 20分 | 必須 |
| コースレビュー | 15分 | 推奨 |
| ドキュメント更新 | 10分 | 推奨 |
| **合計** | **70分** | - |

---

## 関連ファイル

### 変更対象
- `src/env/minicar_env.py` - メイン実装
- `tests/test_env.py` - テスト追加（推奨）

### レビュー対象
- `courses/easy/simple_oval.json`
- `courses/medium/narrow_oval.json`
- `courses/hard/s_curve.json`
- `courses/hard/tight_oval.json`
- `courses/real/*.json`

### ドキュメント
- `CLAUDE.md` - 報酬設計セクション
- `doc/plan/checkpoint-sequential-implementation.md` - 本ドキュメント

---

## 承認

この実装計画で進めてよろしいでしょうか？

確認事項:
1. チェックポイントは必ず順番通り（0→1→2→...）でよいか
2. 既存の学習済みモデルは破棄してよいか
3. すぐに実装を開始してよいか
