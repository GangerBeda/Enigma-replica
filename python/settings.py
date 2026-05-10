# settings.py
# Configuration persistence for the Raspberry Pi Pico.
#
# Loads and saves settings.json from the Pico filesystem and builds the
# machine from it.

import json

# Historical Enigma wiring tables
ROTOR_WIRINGS = {
    "I":   ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q"),
    "II":  ("AJDKSIRUXBLHWTMCQGZNPYFVOE", "E"),
    "III": ("BDFHJLCPRTXVZNYEIWGAKMUSQO", "V"),
    "IV":  ("ESOVPZJAYQUIRHXLNFTGKDCMWB", "J"),
    "V":   ("VZBRGITYUPSDNHLXAWMJQOFECK", "Z"),
}

# Reflector wirings
REFLECTOR_WIRINGS = {
    "UKW-A": "EJMZALYXVBWFCRQUONTSPIKHGD",
    "UKW-B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
    "UKW-C": "RDOBJNTKVEHMLFCWZAXGYIPSUQ",
}

_SETTINGS_FILE = "settings.json"

# Defaults settings
_DEFAULTS = {
    "rotors":    ["I", "II", "III"],
    "positions": ["A", "A", "A"],
    "reflector": "UKW-B",
    "plugboard": [],
}


def load_settings():
    """Return the settings dict. In case of error, fallback to default settings."""
    try:
        with open(_SETTINGS_FILE, "r") as f:
            data = json.loads(f.read())
        return data
    except Exception:
        return {k: list(v) if isinstance(v, list) else v
                for k, v in _DEFAULTS.items()}


def save_settings(settings):
    with open(_SETTINGS_FILE, "w") as f:
        f.write(json.dumps(settings))


def build_enigma(settings):
    """Build and return the enigma machine components based on the settings."""
    from enigma import Rotor, Reflector, Plugboard, RotorSystem

    # ── Plugboard ─────────────────────────────────────────────────────────────
    plugboard = Plugboard()
    for pair in settings.get("plugboard", []):
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            plugboard.connect(str(pair[0]).upper(), str(pair[1]).upper())

    # ── Rotors (left → right in display order) ────────────────────────────────
    default_names = _DEFAULTS["rotors"]
    rotor_names = settings.get("rotors", default_names)

    display_rotors = []
    for i in range(3):
        name = rotor_names[i] if i < len(rotor_names) else default_names[i]
        if name not in ROTOR_WIRINGS:
            name = default_names[i]
        wiring, notch = ROTOR_WIRINGS[name]
        display_rotors.append(Rotor(wiring, notch))

    # ── Initial rotor positions ───────────────────────────────────────────────
    positions = settings.get("positions", _DEFAULTS["positions"])
    for i, pos in enumerate(positions[:3]):
        if isinstance(pos, str) and len(pos) >= 1:
            display_rotors[i].position = (ord(pos[0].upper()) - ord('A')) % 26

    # ── Reflector ─────────────────────────────────────────────────────────────
    refl_name   = settings.get("reflector", "UKW-B")
    refl_wiring = REFLECTOR_WIRINGS.get(refl_name, REFLECTOR_WIRINGS["UKW-B"])
    reflector   = Reflector(refl_wiring)

    # RotorSystem expects [rightmost(fast), middle, leftmost] at indices 0,1,2.
    rotor_system = RotorSystem(list(reversed(display_rotors)), reflector)

    return plugboard, rotor_system, display_rotors
