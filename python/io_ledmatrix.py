# io_ledmatrix.py
# PCF8574 based LED matrix output for Raspberry Pi Pico.
#
# Hardware wiring:
#   I2C1 : SDA = GP14, SCL = GP15
#
#   PCF8574 0x22  (columns 1-6)
#     P0=col1   P1=col2   P2=col3   P3=col4   P4=col5   P5=col6
#
#   PCF8574 0x23  (columns 7-9 + rows 1-3)
#     P0=col7   P1=col8   P2=col9   P5=row1   P6=row2   P7=row3
#
# LED drive convention:
#   LED at intersection lights when:
#     Its ROW pin is HIGH (PCF8574 sourcing current)
#     Its COL pin is LOW  (PCF8574 sinking current)
#
# Letter mapping:
#   Row 0 : cols 0-8    =>  Q W E R T Z U I O
#   Row 1 : cols 1-8    =>   A S D F G H J K        col 0 = SKIP;
#   Row 2 : cols 0-8    =>  P Y X C V B N M L
#
#   Mirrors KEY_MAP in io_keyboard.py

from machine import I2C, Pin

_ADDR_22 = 0x22
_ADDR_23 = 0x23

# all LEDs off values for each expander:
#   0x22: all col pins HIGH
#   0x23: col7-9 HIGH, unused HIGH, rows LOW
_ALL_OFF_22 = 0xFF
_ALL_OFF_23 = 0x1F

LETTER_TO_POS = {
    'A': (1, 1), 'B': (2, 5), 'C': (2, 3), 'D': (1, 3), 'E': (0, 2),
    'F': (1, 4), 'G': (1, 5), 'H': (1, 6), 'I': (0, 7), 'J': (1, 7),
    'K': (1, 8), 'L': (2, 8), 'M': (2, 7), 'N': (2, 6), 'O': (0, 8),
    'P': (2, 0), 'Q': (0, 0), 'R': (0, 3), 'S': (1, 2), 'T': (0, 4),
    'U': (0, 6), 'V': (2, 4), 'W': (0, 1), 'X': (2, 2), 'Y': (2, 1),
    'Z': (0, 5),
}


class LEDMatrix:
    """Controls the LED matrix."""

    def __init__(self, invert=False):
        """Initialise the LED matrix driver."""
        self._i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=100_000)
        self._invert = invert
        self.clear()

    def _write(self, addr, val):
        byte_val = (val ^ 0xFF) & 0xFF if self._invert else val & 0xFF
        self._i2c.writeto(addr, bytes([byte_val]))


    def clear(self):
        """Turn off all LEDs."""
        self._write(_ADDR_22, _ALL_OFF_22)
        self._write(_ADDR_23, _ALL_OFF_23)

    def light(self, letter):
        """Light one LED for selected letter."""
        # clear first
        self.clear()

        pos = LETTER_TO_POS.get(letter.upper() if letter else '')
        if pos is None:
            return

        row, col = pos

        # set row bit to HIGH
        row_bit = 1 << (5 + row)

        if col <= 5:
            # Column is on 0x22, drive only it LOW
            val22 = 0xFF & ~(1 << col)
            val23 = _ALL_OFF_23 | row_bit
        else:
            # Column is on 0x23: drive P(col-6) LOW.
            val22 = 0xFF
            col_bit = 1 << (col - 6)
            col23 = 0x07 & ~col_bit
            val23 = col23 | 0x18 | row_bit

        self._write(_ADDR_22, val22)
        self._write(_ADDR_23, val23)
