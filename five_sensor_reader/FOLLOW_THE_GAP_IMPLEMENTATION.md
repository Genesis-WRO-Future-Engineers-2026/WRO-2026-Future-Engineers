# Follow the Gap アルゴリズム実装計画

## 概要

現在の**壁追従（Wall Following）ロジック**を**Follow the Gap**アルゴリズムに変更する。
Follow the Gap は、センサーデータから最も空いている方向（ギャップ）を検出し、その方向へ進むシンプルで効果的な障害物回避手法。

### 設計方針

- **P 制御のみ採用**: PID 制御は調整が難しいため、シンプルな P（比例）制御のみを使用
- **5 センサー向け簡略化**: 360° LiDAR 向けのフルスペック版ではなく、5 センサー構成に最適化

### 変更の背景

| 現在（壁追従）           | 変更後（Follow the Gap）     |
| ------------------------ | ---------------------------- |
| 壁の直線を幾何学的に推定 | 開けた空間（ギャップ）を検出 |
| 左右壁への追従が目的     | 障害物回避＋経路選択が目的   |
| モード切り替えが複雑     | 統一的なロジックで処理       |
| PID 制御（調整が複雑）   | P 制御のみ（シンプル）       |

---

## タスク一覧

### Phase 1: 新規クラス作成

#### Task 1.1: GapFinder クラスの作成

**ファイル**: `GapFinder.h`, `GapFinder.cpp`（新規作成）

**内容**:

- `Gap` 構造体の定義（開始角度、終了角度、中心角度、幅、最小距離）
- `GapResult` 構造体の定義（最適ギャップ、目標角度、ギャップ数）
- `GapFinder` クラスの実装
  - `find(const SensorData* sensorData)` メイン処理
  - `_inflateObstacles()` 障害物膨張処理
  - `_findGaps()` ギャップ検出
  - `_selectBestGap()` 最適ギャップ選択

**アルゴリズム概要**:

```
1. 各センサーの距離を取得
2. 障害物膨張（安全マージン適用）
3. 連続する「開いた空間」をギャップとして検出
4. ギャップの幅・距離・前方優先度でスコアリング
5. 最高スコアのギャップ中心を目標方向として返す
```

---

### Phase 2: 設定値の追加

#### Task 2.1: Config.h に Follow the Gap 用パラメータを追加

**ファイル**: `Config.h`

**追加内容**:

```cpp
// ============================================================================
// Follow the Gap パラメータ
// ============================================================================
const float OBSTACLE_THRESHOLD = 500.0;         // 障害物判定閾値（mm）
const float OBSTACLE_INFLATION_RADIUS = 150.0;  // 障害物膨張半径（mm）
const float MIN_GAP_WIDTH_ANGLE = 30.0;         // 最小通過可能ギャップ幅（度）
const float GAP_WEIGHT_DISTANCE = 0.3;          // ギャップ選択時の距離重み
const float GAP_WEIGHT_WIDTH = 0.4;             // ギャップ選択時の幅重み
const float GAP_WEIGHT_FORWARD = 0.3;           // ギャップ選択時の前方優先重み

// ============================================================================
// P制御パラメータ（PID → P制御に簡略化）
// ============================================================================
const float STEERING_KP = 0.5;                  // 比例ゲイン（ギャップ角度→ステアリング角度）
```

---

### Phase 3: 既存クラスの修正

#### Task 3.1: SteeringController の簡略化（PID → P 制御）

**ファイル**: `SteeringController.h`, `SteeringController.cpp`

**変更内容**:

- `calculate(const WallDetection& walls)` → `calculate(const GapResult& gap)` に変更
- **PIDController クラスを削除し、シンプルな P 制御に置き換え**
- エラー計算を「ギャップ中心方向への偏差」に変更
- 既存のモード切り替えロジック（MODE_BOTH_WALLS 等）を削除

**変更後のステアリング計算（P 制御）**:

```cpp
float SteeringController::calculate(const GapResult& gap) {
    // P制御: ステアリング角 = Kp × ギャップ中心角度
    float steering = STEERING_KP * gap.target_angle;

    // ステアリング角を制限
    steering = constrain(steering, -MAX_STEERING_ANGLE, MAX_STEERING_ANGLE);

    return steering;
}
```

**P 制御のメリット**:

- 調整パラメータが 1 つだけ（Kp）
- 動作が直感的で理解しやすい
- オーバーシュートや振動が発生しにくい

#### Task 3.2: PIDController クラスの削除

**ファイル**: `PIDController.h`, `PIDController.cpp`

**操作**: 削除（Phase 5 で実施）

#### Task 3.3: Logger にギャップ情報出力を追加

**ファイル**: `Logger.h`

**追加内容**:

- `logGapResult(const GapResult& gap)` メソッド追加
- デバッグ用にギャップ数、最適ギャップの角度・幅を出力

---

### Phase 4: メインプログラムの修正

#### Task 4.1: five_sensor_reader.ino の修正

**ファイル**: `five_sensor_reader.ino`

**変更内容**:

```cpp
// Before
#include "WallDetector.h"
#include "PIDController.h"
WallDetector wallDetector;
WallDetection walls = wallDetector.detect(sensorData);
float steering = steeringController.calculate(walls);

// After
#include "GapFinder.h"
GapFinder gapFinder;
GapResult gap = gapFinder.find(sensorData);
float steering = steeringController.calculate(gap);  // P制御
```

- 緊急停止ロジックは維持（前方センサー < 200mm）
- ログ出力を `logWallDetection` → `logGapResult` に変更
- PIDController のインクルードと使用を削除

---

### Phase 5: 不要ファイルの削除

#### Task 5.1: WallDetector の削除

**ファイル**: `WallDetector.h`, `WallDetector.cpp`

**操作**: 削除

```bash
rm WallDetector.h WallDetector.cpp
```

#### Task 5.2: PIDController の削除

**ファイル**: `PIDController.h`, `PIDController.cpp`

**操作**: 削除

```bash
rm PIDController.h PIDController.cpp
```

---

## ファイル変更サマリー

| ファイル                 | 操作     | 優先度 |
| ------------------------ | -------- | ------ |
| `GapFinder.h`            | 新規作成 | ★★★    |
| `GapFinder.cpp`          | 新規作成 | ★★★    |
| `Config.h`               | 追加     | ★★★    |
| `SteeringController.h`   | 大幅修正 | ★★★    |
| `SteeringController.cpp` | 大幅修正 | ★★★    |
| `five_sensor_reader.ino` | 修正     | ★★★    |
| `Logger.h`               | 追加     | ★★     |
| `WallDetector.h/cpp`     | 削除     | ★      |
| `PIDController.h/cpp`    | 削除     | ★      |

---

## 5 センサー向け簡略化アルゴリズム

フルスペックの Follow the Gap（360° LiDAR 向け）ではなく、5 センサー構成に最適化した簡略版を実装：

### センサー配置

```
        [2] 0°
       /     \
    [1] -20°  [3] +20°
    /           \
[0] -70°      [4] +70°
```

### 簡略化アルゴリズム

```
Step 1: 距離判定
  各センサー距離 > OBSTACLE_THRESHOLD → OPEN
  各センサー距離 ≤ OBSTACLE_THRESHOLD → BLOCKED

Step 2: ギャップ検出
  連続するOPENをギャップとして検出
  例: [BLOCKED, OPEN, OPEN, OPEN, BLOCKED] → 1つのギャップ（-20°〜+20°）

Step 3: ギャップスコアリング
  score = width_weight * ギャップ幅
        + distance_weight * ギャップ内最小距離
        + forward_weight * (1 - |中心角度| / 70°)

Step 4: 最適ギャップ選択
  最高スコアのギャップ中心方向を目標とする

Step 5: P制御でステアリング
  steering = Kp × target_angle
```

---

## P 制御の設計

### なぜ P 制御のみか

| 制御方式   | メリット                           | デメリット               |
| ---------- | ---------------------------------- | ------------------------ |
| **P 制御** | シンプル、調整が容易、安定しやすい | 定常偏差が残る可能性     |
| PID 制御   | 定常偏差なし、高精度               | 調整が複雑、振動しやすい |

Follow the Gap では、目標は「ギャップ中心方向へ向かう」ことであり、壁追従のように厳密な位置制御は不要。
そのため、シンプルな P 制御で十分な性能が得られる。

### P 制御パラメータの調整方法

```
1. Kp = 0.3 から開始（控えめな値）
2. 直線コースで走行テスト
3. ギャップ方向への追従が遅い → Kp を上げる（0.1ずつ）
4. ステアリングが振動する → Kp を下げる
5. 推奨範囲: 0.3 〜 0.8
```

### ステアリング計算式

```cpp
// ギャップ中心角度（度）からステアリング角度（度）を計算
float steering = STEERING_KP * gap.target_angle;

// 例: target_angle = 20°, Kp = 0.5 の場合
// steering = 0.5 × 20° = 10°（右に10°ステアリング）
```

---

## 検討事項

### 1. センサー分解能の制限

| 課題                      | 対策                                          |
| ------------------------- | --------------------------------------------- |
| センサー間隔が 40° と粗い | 線形補間でセンサー間を推定                    |
| 狭いギャップの見落とし    | MIN_GAP_WIDTH_ANGLE を 2 センサー分以上に設定 |
| ギャップ中心の不正確さ    | 前方優先ヒューリスティックを導入              |

### 2. P 制御ゲインの調整

| パラメータ | 推奨初期値 | 調整範囲 | 備考                 |
| ---------- | ---------- | -------- | -------------------- |
| Kp         | 0.5        | 0.3〜0.8 | 大きいほど反応が鋭敏 |

### 3. 緊急停止との統合

現在の緊急停止（前方 < 200mm）は維持しつつ、Follow the Gap と協調：

- ギャップが見つからない場合 → 最も距離が遠い方向へ回避
- 全センサーが近距離 → 緊急停止

---

## テスト計画

### 単体テスト

1. **GapFinder テスト**

   - 様々なセンサーパターンでギャップ検出を確認
   - 障害物膨張が正しく機能するか確認
   - スコアリングが期待通りか確認

2. **SteeringController テスト**
   - GapResult 入力でステアリング角が正しく計算されるか
   - P 制御の動作確認（Kp × target_angle）

### 実機テスト

1. **直線コース**: 前方ギャップを維持して直進
2. **L 字コーナー**: コーナー内側のギャップを検出して曲がる
3. **T 字路**: 最も広いギャップを選択して進む
4. **障害物回避**: 障害物を避けてギャップ方向へ進む

### P 制御チューニング手順

1. Kp = 0.3 で開始
2. 直線コースで追従テスト
3. 反応が遅ければ Kp を +0.1
4. 振動すれば Kp を -0.1
5. 最適値を Config.h に記録

---

## 実装スケジュール（目安）

| Phase   | 内容                                  | 工数目安 |
| ------- | ------------------------------------- | -------- |
| Phase 1 | GapFinder クラス作成                  | 2-3 時間 |
| Phase 2 | Config.h 修正                         | 15 分    |
| Phase 3 | SteeringController 簡略化（P 制御化） | 30 分    |
| Phase 4 | メインプログラム修正                  | 30 分    |
| Phase 5 | 不要ファイル整理                      | 15 分    |
| テスト  | 単体テスト＋ Kp 調整                  | 1-2 時間 |

**合計**: 約 5-7 時間

---

## 参考資料

- [Follow the Gap Method (MIT)](https://github.com/f1tenth/f1tenth_labs)
- [Disparity Extender Algorithm](https://www.nathanotterness.com/2019/04/the-disparity-extender-algorithm-and.html)
