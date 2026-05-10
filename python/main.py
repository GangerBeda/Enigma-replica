# main.py
# Enigma machine entry point for Raspberry Pi Pico.
#
# Wiring summary:
#   Keyboard  I2C0 : SDA=GP0  SCL=GP1   expanders 0x20, 0x21
#   LED matrix I2C1: SDA=GP14 SCL=GP15  expanders 0x22, 0x23
#   LCD1602 SoftI2C: SDA=GP10 SCL=GP11  backpack 0x27

# Debug: when true, the lampboard class prints status over USB serial.
DEBUG = True

LED_MATRIX_INVERT = True

from enigma import Lampboard
from io_keyboard import KeyboardMatrix
from io_ledmatrix import LEDMatrix
from lcd1602_pcf8574 import LCD1602
from settings import load_settings, build_enigma
from web_server import connect_wifi, run_web_server
import _thread


def main():

    # Load persisted settings and build the machine
    settings = load_settings()
    
    # display_rotors[0] = left rotor, [1] = middle, [2] = right (fast)
    plugboard, rotor_system, display_rotors = build_enigma(settings)

    lampboard = Lampboard()

    # Hardware I/O
    keyboard  = KeyboardMatrix()
    led_matrix = LEDMatrix(invert=LED_MATRIX_INVERT)
    lcd       = LCD1602(sda_pin=10, scl_pin=11, address=0x27, cols=16, rows=2)
    lcd_ready = lcd.begin()
    last_lcd_positions = None

    # Initial display
    if DEBUG:
        lampboard.update_output(' ', ' ', plugboard)
        lampboard.display_rotor_states(display_rotors)
        if not lcd_ready:
            print("LCD1602 init failed on SoftI2C GP10/GP11 0x27.")

    if lcd_ready:
        last_lcd_positions = lcd.show_positions(
            [r.get_position() for r in display_rotors],
            last_positions=last_lcd_positions
        )

    # Wi-Fi + web configuration server
    ip = ""
    try:
        ip = connect_wifi()
        if ip:
            print("Web UI at http://{}/".format(ip))
            _thread.start_new_thread(run_web_server, (settings, ip))
        else:
            print("Web UI unavailable (no Wi-Fi connection).")
    except Exception as e:
        print("Wi-Fi / web server start failed:", e)
        ip = ""

    if lcd_ready:
        lcd.show_wifi_status(ip)

    print("Enigma machine ready – press a key.")



    # Main loop
    while True:
        # Read input from Keyboard
        user_input = keyboard.read_key()

        # Encryption path
        plugboard_output = plugboard.route(user_input)
        encrypted_char   = rotor_system.encrypt_char(plugboard_output)
        encrypted_char   = plugboard.route(encrypted_char)

        # Show output on Lampboard
        led_matrix.light(encrypted_char)

        if DEBUG:
            lampboard.update_output(user_input, encrypted_char, plugboard)
            lampboard.display_rotor_states(display_rotors)

        # Update rotor state display
        if lcd_ready:
            last_lcd_positions = lcd.show_positions(
                [r.get_position() for r in display_rotors],
                last_positions=last_lcd_positions
            )


main()
