# LCD1602 display driver
# Hardware wiring:
#   I2C0 : SDA = GP10, SCL = GP11

from machine import Pin, SoftI2C
import time


class LCD1602:
    RS = 0x01
    E = 0x04
    BL = 0x08

    def __init__(self, sda_pin=10, scl_pin=11, address=0x27, cols=16, rows=2, freq=100000):
        self.address = address
        self.cols = cols
        self.rows = rows
        self._i2c = SoftI2C(sda=Pin(sda_pin), scl=Pin(scl_pin), freq=freq)
        self._initialized = False

    def begin(self):
        try:
            if self.address not in self._i2c.scan():
                return False
            time.sleep_ms(50)
            self._write4(0x03, mode=0)
            time.sleep_ms(5)
            self._write4(0x03, mode=0)
            time.sleep_us(150)
            self._write4(0x03, mode=0)
            time.sleep_us(150)
            self._write4(0x02, mode=0)

            self._command(0x28)  # 4-bit, 2-line, 5*8 dots
            self._command(0x0C)  # display on, cursor off
            self.clear()
            self._command(0x06)  # entry mode
            self._initialized = True
            return True
        except OSError:
            return False

    def clear(self):
        self._command(0x01)
        time.sleep_ms(2)

    def set_cursor(self, row, col):
        row_offsets = (0x00, 0x40)
        if row >= self.rows:
            row = self.rows - 1
        if col >= self.cols:
            col = self.cols - 1
        self._command(0x80 | (row_offsets[row] + col))

    def write_text(self, row, col, text):
        if not self._initialized:
            return
        self.set_cursor(row, col)
        for ch in text:
            self._send(ord(ch), mode=1)

    def show_wifi_status(self, ip=""):
        """
        Write Wi-Fi status to the first LCD line (row 0).

        If connected, show IP address.
        The text is always padded to erase any previous content on that line.
        """
        if not self._initialized:
            return
        if ip:
            raw = ip
        else:
            raw = "Not connected"
        line = raw[:self.cols]
        line += ' ' * (self.cols - len(line))
        self.write_text(0, 0, line)

    def show_positions(self, positions, last_positions=None):
        """Write rotor positions to the LCD display."""
        if not self._initialized:
            return last_positions

        normalized_positions = []
        for p in positions:
            s = str(p).strip()
            normalized_positions.append(s[0].upper() if s else '?')

        position_str = " ".join(normalized_positions)
        if position_str == last_positions:
            return last_positions

        line_raw = ("POS: " + position_str)[:self.cols]
        line = line_raw + ' ' * (self.cols - len(line_raw))
        if self.rows > 1:
            self.write_text(1, 0, line)
        return position_str

    def _write_byte(self, value):
        self._i2c.writeto(self.address, bytes([value & 0xFF]))

    def _pulse_enable(self, data):
        self._write_byte(data | self.E)
        time.sleep_us(1)
        self._write_byte(data & ~self.E)
        time.sleep_us(50)

    def _write4(self, nibble, mode):
        data = ((nibble & 0x0F) << 4) | self.BL
        if mode:
            data |= self.RS
        self._write_byte(data)
        self._pulse_enable(data)

    def _send(self, value, mode):
        self._write4((value >> 4) & 0x0F, mode)
        self._write4(value & 0x0F, mode)

    def _command(self, cmd):
        self._send(cmd, mode=0)
