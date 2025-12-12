"""シリアル通信モジュール - ArduinoへPWMパルス幅を送信"""

import serial
import time
from typing import Optional

from config import (
    SERIAL_PORT,
    SERIAL_BAUDRATE,
    SERIAL_TIMEOUT,
    SERVO_MIN_PULSE_WIDTH_US,
    SERVO_MAX_PULSE_WIDTH_US,
    ESC_MIN_PULSE_WIDTH_US,
    ESC_MAX_PULSE_WIDTH_US
)


class ArduinoSerial:
    """
    Arduinoとシリアル通信でパルス幅を送受信するクラス

    通信プロトコル:
        サーボ: "S<パルス幅μs>" 例: "S1500" → 1500マイクロ秒
        ESC:   "E<パルス幅μs>" 例: "E1500" → 1500マイクロ秒
    """

    def __init__(self, port: str = SERIAL_PORT, baudrate: int = SERIAL_BAUDRATE, timeout: float = SERIAL_TIMEOUT):
        """
        シリアルポートを初期化

        Parameters:
            port: シリアルポート名（デフォルト: config.SERIAL_PORT）
            baudrate: ボーレート（デフォルト: config.SERIAL_BAUDRATE）
            timeout: タイムアウト時間（秒、デフォルト: config.SERIAL_TIMEOUT）
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self._connect()

    def _connect(self):
        """シリアルポートに接続"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            # Arduinoのリセット待ち（シリアル接続時にArduinoがリセットされる）
            time.sleep(2)
            print(f"Serial connected: {self.port} @ {self.baudrate}bps")
        except serial.SerialException as e:
            print(f"Failed to open serial port {self.port}: {e}")
            self.serial_connection = None

    def send_servo_pulse(self, pulse_width_us: int) -> bool:
        """
        サーボ用パルス幅をArduinoに送信

        Parameters:
            pulse_width_us: パルス幅（マイクロ秒）

        Returns:
            送信成功時True、失敗時False
        """
        # パルス幅の範囲チェック（config.pyの設定範囲内に制限）
        pulse_width_us = max(SERVO_MIN_PULSE_WIDTH_US, min(SERVO_MAX_PULSE_WIDTH_US, pulse_width_us))

        command = f"S{pulse_width_us}\n"
        return self._send_command(command)

    def send_esc_pulse(self, pulse_width_us: int) -> bool:
        """
        ESC用パルス幅をArduinoに送信

        Parameters:
            pulse_width_us: パルス幅（マイクロ秒）

        Returns:
            送信成功時True、失敗時False
        """
        # パルス幅の範囲チェック（config.pyの設定範囲内に制限）
        pulse_width_us = max(ESC_MIN_PULSE_WIDTH_US, min(ESC_MAX_PULSE_WIDTH_US, pulse_width_us))

        command = f"E{pulse_width_us}\n"
        return self._send_command(command)

    def _send_command(self, command: str) -> bool:
        """
        コマンドをシリアルポートに送信

        Parameters:
            command: 送信するコマンド文字列

        Returns:
            送信成功時True、失敗時False
        """
        if self.serial_connection is None or not self.serial_connection.is_open:
            print("Serial connection not available")
            return False

        try:
            self.serial_connection.write(command.encode('utf-8'))
            self.serial_connection.flush()
            return True
        except serial.SerialTimeoutException:
            print(f"Serial write timeout: {command.strip()}")
            return False
        except Exception as e:
            print(f"Serial write error: {e}")
            return False

    def close(self):
        """シリアルポートを閉じる"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Serial connection closed")

    def __del__(self):
        """デストラクタ - シリアルポートを確実に閉じる"""
        self.close()
