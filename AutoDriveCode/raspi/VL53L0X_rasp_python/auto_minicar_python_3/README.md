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

- **Sensor 1**: -70° (左)
- **Sensor 2**: -20°
- **Sensor 3**: 0° (正面)
- **Sensor 4**: +20°
- **Sensor 5**: +70° (右)

## プロジェクト構成

```
auto_minicar_python_3/
├── config.py                # 設定ファイル（GPIO、センサー、制御パラメータ）
├── geometry.py              # 幾何計算（Point, Line クラス）
├── sensors.py               # センサー管理（SensorManager クラス）
├── actuators.py             # アクチュエーター制御（Actuator クラス）
├── steering_controller.py   # ステアリング制御（SteeringController クラス）
├── main.py                  # メインプログラム（AutoDriveCar クラス）
├── test_*.py                # テストファイル
├── Makefile                 # ビルドコマンド
└── README.md                # このファイル
```

## 動作原理

1. **センサー読み取り**: 5つのVL53L0Xセンサーから距離を測定
2. **壁検出**: 左右2つずつのセンサーから壁の直線を計算
3. **交点計算**: 各壁の直線とy軸（車体正面方向）の交点を求める
4. **ステアリング判断**:
   - 両壁検出: 左右の交点の差からステアリング角度を計算
   - 片側のみ: 開けている方向へステアリング
   - 壁なし: 直進

## 使用方法

### 実行

```bash
make run
```

または

```bash
sudo python3 main.py
```

### テスト実行

```bash
make test
```

テストにはpytestが必要です:

```bash
pip install pytest
```

## 設定

`config.py` で以下を設定可能:

- **GPIO ピン番号**: センサーシャットダウンピン、サーボ、ESC
- **I2C アドレス**: 各センサーのアドレス
- **センサー角度**: 各センサーの取り付け角度
- **ステアリングパラメータ**: 最大角度、ゲイン、比率

## ハードウェア要件

- Raspberry Pi (GPIO 制御可能なモデル)
- VL53L0X 距離センサー × 5
- サーボモーター（ステアリング用）
- ESC（モーター制御用）

## ライセンス

MIT License (Copyright (c) 2017 John Bryan Moore)
