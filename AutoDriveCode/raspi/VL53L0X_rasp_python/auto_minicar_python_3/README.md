# 5-Sensor Auto Drive System

5つのVL53L0X距離センサーを使用した自動運転ミニカーシステム

## センサー配置

```
        正面 (0°)
           |
    -20°   |   +20°
      \    |    /
       \   |   /
-70°    \  |  /    +70°
(左)     \ | /     (右)
```

| センサー | 角度 | 位置 |
|---------|------|------|
| Sensor 1 | -70° | 左 |
| Sensor 2 | -20° | 左前 |
| Sensor 3 | 0° | 正面 |
| Sensor 4 | +20° | 右前 |
| Sensor 5 | +70° | 右 |

## 動作原理

1. **センサー読み取り**: 5つのVL53L0Xセンサーから距離を測定
2. **壁検出**: 左右2つずつのセンサーから壁の直線を計算
3. **交点計算**: 各壁の直線とy軸（車体正面方向）の交点を求める
4. **ステアリング判断**:
   - 両壁検出: 左右の交点の差からステアリング角度を計算
   - 片側のみ: 開けている方向へステアリング
   - 壁なし: 直進

## 使い方

### ヘルプ表示

```bash
make
# または
make help
```

### 実行（Raspberry Pi上）

```bash
make run
```

### テスト

```bash
# テスト実行
make test

# カバレッジ付き
make test-cov

# デバッグ（コンテナに入る）
make docker-shell
```

## ファイル構成

| ファイル | 説明 |
|---------|------|
| `config.py` | 設定（GPIO、センサー、制御パラメータ） |
| `geometry.py` | 幾何計算（Point, Line クラス） |
| `sensors.py` | センサー管理（SensorManager クラス） |
| `actuators.py` | アクチュエーター制御（Actuator クラス） |
| `steering_controller.py` | ステアリング制御（SteeringController クラス） |
| `main.py` | メインプログラム（AutoDriveCar クラス） |
| `test_*.py` | テストコード（112テストケース） |

## 設定

`config.py` で以下を設定可能:

- **GPIO ピン番号**: センサーシャットダウンピン、サーボ、ESC
- **I2C アドレス**: 各センサーのアドレス（0x2B〜0x30）
- **センサー角度**: 各センサーの取り付け角度
- **ステアリングパラメータ**:
  - `MAX_STEER_ANGLE`: 最大操舵角（30度）
  - `INTERSECTION_DIFF_GAIN`: 交点差からのゲイン（0.1）
  - `ONE_SIDE_OPEN_STEER_RATIO`: 片側開放時の比率（0.5）

## ハードウェア要件

- Raspberry Pi（GPIO制御可能なモデル）
- VL53L0X 距離センサー × 5
- サーボモーター（ステアリング用）
- ESC（モーター制御用）

## ライセンス

MIT License (Copyright (c) 2017 John Bryan Moore)
