# enigma.py
# Core Enigma machine logic
# Rotor, Reflector, Plugboard, RotorSystem, Lampboard


class Rotor:

    def __init__(self, wiring, notch_positions):
        self.wiring = wiring
        self.notch_positions = notch_positions
        self.position = 0

    def rotate(self):
        self.position = (self.position + 1) % 26

    def at_notch(self):
        current_char = chr(ord('A') + self.position)
        return current_char in self.notch_positions

    def is_one_past_notch(self):
        current_char = chr(ord('A') + self.position)
        for notch in self.notch_positions:
            one_past_notch = chr(((ord(notch) - ord('A') + 1) % 26) + ord('A'))
            if current_char == one_past_notch:
                return True
        return False

    def encrypt_forward(self, input_char):
        index = (ord(input_char) - ord('A') + self.position) % 26
        output = self.wiring[index]
        return chr((ord(output) - ord('A') - self.position + 26) % 26 + ord('A'))

    def encrypt_backward(self, input_char):
        index = (ord(input_char) - ord('A') + self.position) % 26
        wiring_index = self.wiring.index(chr(index + ord('A')))
        return chr((wiring_index - self.position + 26) % 26 + ord('A'))

    def get_position(self):
        return chr(ord('A') + self.position)


class Reflector:

    def __init__(self, wiring):
        self.wiring = wiring

    def reflect(self, input_char):
        index = ord(input_char) - ord('A')
        return self.wiring[index]


class Plugboard:

    def __init__(self):
        self.plug_pairs = []  # list of (char, char) tuples

    def route(self, input_char):
        for pair in self.plug_pairs:
            if pair[0] == input_char:
                return pair[1]
            if pair[1] == input_char:
                return pair[0]
        return input_char

    def connect(self, char1, char2):
        # Called twice because each call removes only one colliding pair.
        # If char1 and char2 are each already in different pairs, both must
        # be removed before the new pair can be added.  (Mirrors C# original.)
        self._remove_colliding_pairs(char1, char2)
        self._remove_colliding_pairs(char1, char2)
        self.plug_pairs.append((char1, char2))

    def _remove_colliding_pairs(self, char1, char2):
        for pair in self.plug_pairs:
            if (pair[0] == char1 or pair[1] == char1 or
                    pair[0] == char2 or pair[1] == char2):
                self.plug_pairs.remove(pair)
                return

    def test_pairs(self):
        self.plug_pairs = []
        self.connect('A', 'B')
        self.connect('C', 'D')
        self.connect('E', 'F')
        self.connect('G', 'H')
        self.connect('I', 'J')
        self.connect('K', 'L')


class RotorSystem:
    """Represents enigma's internal mechanism. Serves as the main processing unit for encryption and decryption."""

    def __init__(self, rotors, reflector):
        self.rotors = rotors
        self.reflector = reflector

    def encrypt_char(self, input_char):
        # Rotate rotors before encryption (historical Enigma behavior: the rotor
        # step happens when the key is pressed, before the signal travels through).
        self._rotate_rotors()
        # Pass through rotors forward
        for rotor in self.rotors:
            input_char = rotor.encrypt_forward(input_char)
        # Reflect
        input_char = self.reflector.reflect(input_char)
        # Pass through rotors backward
        for i in range(len(self.rotors) - 1, -1, -1):
            input_char = self.rotors[i].encrypt_backward(input_char)
        return input_char

    def _rotate_rotors(self):
        # Capture notch state for all rotors before any rotation so that one
        # rotor's step cannot affect another rotor's stepping decision.
        at_notch = [r.at_notch() for r in self.rotors]
        # The rightmost rotor (index 0) always steps.
        self.rotors[0].rotate()
        # Each subsequent rotor steps when the rotor to its right was at its
        # notch (normal carry), or when it is itself at its notch and is not the
        # leftmost rotor (double-step anomaly of the real Enigma machine).
        for i in range(1, len(self.rotors)):
            double_step = (i < len(self.rotors) - 1) and at_notch[i]
            if at_notch[i - 1] or double_step:
                self.rotors[i].rotate()


class Lampboard:
    """
    On the MCU, this class provides USB-serial (print) debug output only.
    The physical LED matrix is driven by io_ledmatrix.py.
    Gate all output behind the DEBUG flag in main.py if desired.

    This is a remant of the original console implementation.
    """

    def __init__(self):
        self.output_string = ''
        self.input_string = ''

    def _display_plugboard(self, plugboard):
        print("Plugboard connections: ", end='')
        for pair in plugboard.plug_pairs:
            print("<{}-{}> ".format(pair[0], pair[1]), end='')
        print()

    def display_rotor_states(self, rotors):
        print("Rotor positions: ", end='')
        for r in rotors:
            pos = r.get_position()
            if 'A' <= pos <= 'Z':
                display = pos
            else:
                display = '?'
            print("[{}] ".format(display), end='')
        print()

    def update_output(self, in_letter, lit_letter, plugboard):
        self.output_string += lit_letter
        self.input_string += in_letter
        print("Enigma machine simulator")
        lamp_row = ''
        for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if c == lit_letter:
                lamp_row += '[{}] '.format(c)
            else:
                lamp_row += '{} '.format(c.lower())
        print(lamp_row)
        self._display_plugboard(plugboard)
        print("Input:  " + self.input_string)
        print("Output: " + self.output_string)
