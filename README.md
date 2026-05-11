# Pico Enigma (MicroPython) – quick build & wiring guide

---

## 1) Parts checklist and central circuit setup

- Raspberry Pi Pico W
- 4× PCF8574 I²C GPIO expanders  
  - 2× for keyboard matrix  
  - 2× for LED matrix
- 3×9 key matrix (26 keys) wired as rows/columns
- 3×9 LED matrix / lampboard (26 LEDs, matrix wired)
- LCD1602 (HD44780) with I²C backpack (PCF8574)
  - Commonly available LCD displays with these specifications should fit, but just in case, this is the one used during development: <https://dratek.cz/arduino-platforma/1570-iic-i2c-display-lcd-1602-16x2-znaku-lcd-modul-modry.html>
- Half-sized breadboard, wires
- Resistors ~200 \(\Omega \) for LEDs (For LED matrix at least 3 resistors)

- Put the microcontroller on the breadboard and connect any **GND** and **Vcc** to a bus strip and ground rail of the breadboard, using which you will power the individual subsystems.
- The 'box' model is the main casing component. Facing the front of the model, put the slotted breadboard to the back-right corner of the model.

---

## 2) 3D printed parts

- Print all the 3D parts in the 'Models' directory and its subdirectories.
- The models are made to be printed simply without supports. You can print with PLA, PETG, ABS, or virtually anything, but since some models have a large first layer, I recommend printing with PLA for simplicity and with a brim.
- You can assemble the subsystems along the way.

---

## 3) I²C buses and Pico pins

This project uses **two hardware I²C buses** plus one **SoftI²C**:

### Keyboard expanders (I²C0)
- Pico **GP0 = SDA0**
- Pico **GP1 = SCL0**
- PCF8574 addresses: **0x20** and **0x21**

### LED matrix expanders (I²C1)
- Pico **GP14 = SDA1**
- Pico **GP15 = SCL1**
- PCF8574 addresses: **0x22** and **0x23**

### LCD1602 (SoftI²C, separate)
- Pico **GP10 = SDA**
- Pico **GP11 = SCL**
- LCD backpack address: usually **0x27**

> All devices on the same I²C bus share SDA/SCL, but must have unique addresses.

---

## 4) PCF8574 address setup

PCF8574 boards have address jumpers A0/A1/A2.

Set them so you get:
- Keyboard: **0x20**, **0x21**
- LED: **0x22**, **0x23**
- LCD backpack: **0x27** (fixed by backpack or solder pads)

---

## 5) Keyboard assembly
- Install the key switches onto the 'keyboard' model.
- Wire the keyboard switches together into a matrix according to the following diagram.
              - diagram
- Slot the PCF8574 expanders into the 'keyboard circuitry' model via zipties or adhesive and secure the keyboard circuitry to the keyboard with the 'keyboard pivot'.

Keyboard uses two expanders:

### PCF8574 @ 0x20 (rows + cols 5–8)
- **P7 = row0**
- **P6 = row1**
- **P5 = row2**
- **P4 = col8**
- **P3 = col7**
- **P2 = col6**
- **P1 = col5**
- **P0 = unused**

### PCF8574 @ 0x21 (cols 0–4)
- **P4 = col4**
- **P3 = col3**
- **P2 = col2**
- **P1 = col1**
- **P0 = col0**

How to wire it physically:
- Connect each of the 3 **row wires** from your key matrix to the row pins above.
- Connect each of the 9 **column wires** to col0..col8 pins above.

- This completes the keyboard and you can now insert it into the 'box' casing.

---

## 6) LED “lampboard” assembly

- Print 26 of the 'led cup' models. Each of them has 2 openings at the base for LED terminals, one of which is marked with a + symbol for the anode.
- Prepare your 26 'led cups' by putting an LED in each one.
- Slot the 'led cups' in the 'lampboard frame' and solder them together according to the following diagram

    - diagram

### Circuit setup
LED matrix uses two expanders:

### PCF8574 @ 0x22 (columns 0–5)
- **P0 = col0** (hardware “col1”)
- **P1 = col1**
- **P2 = col2**
- **P3 = col3**
- **P4 = col4**
- **P5 = col5**
- **P6, P7 = unused**

### PCF8574 @ 0x23 (columns 6–8 + rows)
- **P0 = col6**
- **P1 = col7**
- **P2 = col8**
- **P3, P4 = unused**
- **P5 = row0**
- **P6 = row1**
- **P7 = row2**

How to wire it physically:
- Put the PCF8574 expanders in their slot on the 'lampboard circuitry' model and secure it with zip ties or adhesive. Then, attach the slotted lampboard circuitry to the wired lampboard frame.
- Connect the 3 **LED matrix row lines** to P5–P7 of **0x23**.
  - For the 3 rows, connect them to the expander via the 3 resistors. **This is important**, as without them, the LEDs will break.
- Connect LED matrix columns:
  - col0–col5 to **0x22 P0–P5**
  - col6–col8 to **0x23 P0–P2**

Polarity note:
- If **all lamps turn on at boot**, your matrix polarity is inverted relative to the default drive mode. The project has an **invert** option in the driver to fix this without rewiring.

---

## 7) LCD1602 wiring (I²C backpack)
- Slide the display into the 'display slot' model and connect it to the MCU.

- **SDA → GP10**
- **SCL → GP11**
- **VCC/GND** as required by your module
- The characters may not be visible at first. In that case, you can adjust the contrast using a potentiometer on the backpack of the display with a screwdriver.
  - Additionally, if you're powering the display with 3.3 V, you can try switching to 5 V, which should work better with LCD displays.
- Adjust the **contrast potentiometer** on the backpack if the backlight is on but characters are not visible.

- Attach the completed display slot to the lampboard frame.
  - This completes the lampboard. You can now put it into the 'box' casing model.
  - The replica should now be complete. Once you're done wiring the components to the MCU, you can put the 'box back' model on the back of the model and the 'keyboard lid' between the keyboard and the lampboard to seal the machine and the replica is completed.

---

## 8) Loading the program

- ✅ All GND connected together
- ✅ I²C0 devices (0x20, 0x21) on GP0/GP1
- ✅ I²C1 devices (0x22, 0x23) on GP14/GP15
- ✅ LCD on GP10/GP11, address 0x27
- ✅ No address conflicts on any bus
- ✅ No row/column mix-up on keyboard vs lampboard wiring
- ✅ LED current limiting is handled appropriately for your build

That’s it — once the wiring matches the tables above, the MicroPython code should be able to scan keys and light the correct lamp positions.
- The replica has a small opening in the back. Use that to connect the machine to a computer.
- Load all the scripts from the 'python' directory to the root of the MCU file system.
- Edit the 'wifi_config.py' file by inputing the ssid and password to your WiFi. This is needed for configuration.
- Once done, the machine will run the program on startup, connect to the WiFi and display an IP address. On that address on port 80 (http), you'll find a configuration interface, which you can use to configure the machine's initial state.
