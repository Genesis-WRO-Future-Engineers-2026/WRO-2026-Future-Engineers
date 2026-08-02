#Mpu6050.py
import machine

class accel():
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00') # Wake up MPU6050

    def get_raw_values(self):
        a = self.i2c.readfrom_mem(self.addr, 0x3B, 14)
        return a

    def get_values(self):
        raw = self.get_raw_values()
        res = {}
        res["AcX"] = self.bytes_to_int(raw[0], raw[1])
        res["AcY"] = self.bytes_to_int(raw[2], raw[3])
        res["AcZ"] = self.bytes_to_int(raw[4], raw[5])
        res["Tmp"] = self.bytes_to_int(raw[6], raw[7]) / 340.00 + 36.53
        res["GyX"] = self.bytes_to_int(raw[8], raw[9])
        res["GyY"] = self.bytes_to_int(raw[10], raw[11])
        res["GyZ"] = self.bytes_to_int(raw[12], raw[13])
        return res

    def bytes_to_int(self, first_byte, second_byte):
        if not first_byte & 0x80:
            return first_byte << 8 | second_byte
        return -(((first_byte ^ 255) << 8) | (second_byte ^ 255) + 1)
