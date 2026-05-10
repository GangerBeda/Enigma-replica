# io_keyboard.py
# PCF8574 based 3×9 keyboard matrix input for Raspberry Pi Pico.
#
# Hardware wiring:
#   I2C0 : SDA = GP0, SCL = GP1
#
#   PCF8574 0x20  (rows + col 5-8)
#     P7 = row 0       P6 = row 1       P5 = row 2
#     P4 = col 8       P3 = col 7       P2 = col 6       P1 = col 5
#
#   PCF8574 0x21  (col 0-4)
#     P4 = col 4       P3 = col 3       P2 = col 2       P1 = col 1       P0 = col 0
#
# Key layout (mirrors that of the original enigma) => letter
#   Row 0 : cols 0-8    =>  Q W E R T Z U I O
#   Row 1 : cols 1-8    =>   A S D F G H J K        col 0 = SKIP
#   Row 2 : cols 0-8    =>  P Y X C V B N M L
#
# Scanning method:
#   Drive one row pin LOW at a time. Column pins are released HIGH.
#   Read both expanders. A column bit LOW means that key is pressed.
#   Debounce: require two consecutive identical reads separated by 20 ms for signal stability.
#   Wait for full key release before accepting the next press.

from machine import I2C, Pin
import time

_ADDR_20 = 0x20
_ADDR_21 = 0x21

# byte to set selected row to LOW when scanning
_ROW_DRIVE = (
    0b01111111,
    0b10111111,
    0b11011111,
)

# letter mapping (row, column)
KEY_MAP = {
    (0, 0): 'Q', (0, 1): 'W', (0, 2): 'E', (0, 3): 'R', (0, 4): 'T',
    (0, 5): 'Z', (0, 6): 'U', (0, 7): 'I', (0, 8): 'O',

    (1, 1): 'A', (1, 2): 'S', (1, 3): 'D', (1, 4): 'F', (1, 5): 'G',
    (1, 6): 'H', (1, 7): 'J', (1, 8): 'K',
    (2, 0): 'P', (2, 1): 'Y', (2, 2): 'X', (2, 3): 'C', (2, 4): 'V',
    (2, 5): 'B', (2, 6): 'N', (2, 7): 'M', (2, 8): 'L',
}

_DEBOUNCE_MS = 20
_POLL_MS = 5


class KeyboardMatrix:
    """Scans the keyboard matrix and returns A-Z key press"""

    def __init__(self):
        self._i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100_000)
        self._waiting_for_release = False

    def _write(self, addr, val):
        self._i2c.writeto(addr, bytes([val & 0xFF]))

    def _read(self, addr):
        return self._i2c.readfrom(addr, 1)[0]

    def _scan_once(self):
        """Return (row, col) for the first pressed key found"""
        for row in range(3):
            # drive selected row LOW, release all col pins (set HIGH = input)
            self._write(_ADDR_20, _ROW_DRIVE[row])
            self._write(_ADDR_21, 0xFF)
            time.sleep_us(100)

            val21 = self._read(_ADDR_21)
            val20 = self._read(_ADDR_20)

            # Check col 0-4
            for col in range(5):
                if not (val21 & (1 << col)):
                    if (row, col) != (1, 0):
                        return (row, col)

            # check col 5-8
            for offset in range(4):
                if not (val20 & (1 << (offset + 1))):
                    return (row, 5 + offset)

        return None

    def _all_released(self):
        """Return true when no key is pressed."""
        return self._scan_once() is None


    def read_key(self):
        """Returns the letter corresponding to the pressed key."""
        # wait for no keys pressed
        if self._waiting_for_release:
            while not self._all_released():
                time.sleep_ms(_POLL_MS)
            self._waiting_for_release = False
            time.sleep_ms(_DEBOUNCE_MS)

        # Wait for a new press
        while True:
            key = self._scan_once()
            if key is not None:
                time.sleep_ms(_DEBOUNCE_MS)
                if self._scan_once() == key:
                    letter = KEY_MAP.get(key)
                    if letter is not None:
                        self._waiting_for_release = True
                        return letter
            time.sleep_ms(_POLL_MS)
