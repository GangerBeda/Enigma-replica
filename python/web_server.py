# web_server.py
# Lightweight HTTP configuration server for the Enigma Pico.
#
# Serves a single-page web UI that lets the user set rotors, reflector, rotor positions and plugboard pairs.
# Applying the configuration saves the new settings to settings.json and calls
# machine.reset() so main.py picks them up immediately on the next boot.

import socket
import time
import machine

from settings import save_settings, ROTOR_WIRINGS, REFLECTOR_WIRINGS

def _url_decode(s):
    """Percent-decode a URL-encoded string to a string."""
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '+':
            out.append(' ')
            i += 1
        elif ch == '%' and i + 2 < len(s):
            try:
                out.append(chr(int(s[i + 1:i + 3], 16)))
                i += 3
            except ValueError:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
    return ''.join(out)


def _parse_form(body):
    """Parse application/x-www-form-urlencoded body to settings dict."""
    params = {}
    for part in body.split('&'):
        if '=' in part:
            k, v = part.split('=', 1)
            params[_url_decode(k)] = _url_decode(v)
    return params


_ROTOR_NAMES    = list(ROTOR_WIRINGS.keys())        # ["I", "II", "III", "IV", "V"]
_REFLECTOR_NAMES = list(REFLECTOR_WIRINGS.keys())   # ["UKW-A", "UKW-B", "UKW-C"]
_LETTERS        = [chr(65 + i) for i in range(26)]


def _select(name, options, selected):
    """Return an HTML <select> element string."""
    parts = ['<select name="', name, '">']
    for opt in options:
        sel = ' selected' if opt == selected else ''
        parts += ['<option value="', opt, '"', sel, '>', opt, '</option>']
    parts.append('</select>')
    return ''.join(parts)


def _build_page(settings, ip=""):
    """Return the full configuration page as a UTF-8 HTML string."""
    rotors    = settings.get("rotors",    ["I", "II", "III"])
    positions = settings.get("positions", ["A", "A", "A"])
    reflector = settings.get("reflector", "UKW-B")
    pairs     = settings.get("plugboard", [])

    # Plugboard pair badges with individual Remove forms
    pairs_html = []
    for pair in pairs:
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            plug_val = str(pair[0]).upper() + str(pair[1]).upper()
            pairs_html.append(
                '<form method="post" style="display:inline;margin:2px">'
                '<input type="hidden" name="action" value="remove_plug">'
                '<input type="hidden" name="plug" value="{v}">'
                '<button type="submit" class="pair-btn">'
                '{a}&#8596;{b} &#x2715;'
                '</button>'
                '</form>'.format(v=plug_val, a=pair[0], b=pair[1])
            )
    if not pairs_html:
        pairs_html = ['<em style="color:#888">No plugboard pairs.</em>']

    ip_line = (
        '<p class="note">Web UI address: '
        '<strong>http://{}/</strong></p>'.format(ip)
    ) if ip else ''

    r = rotors
    p = positions

    parts = [
        '<!DOCTYPE html><html><head><title>Enigma Config</title>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<style>',
        'body{font-family:sans-serif;max-width:520px;margin:20px auto;padding:0 12px}',
        'h2{margin:18px 0 6px;padding-bottom:3px;border-bottom:1px solid #ccc}',
        'table{border-collapse:collapse;width:100%}',
        'th,td{padding:5px 8px;text-align:center}',
        'th{font-size:0.82em;color:#555;font-weight:normal}',
        'select{font-size:1em;padding:2px}',
        '.apply-btn{margin-top:16px;padding:9px 20px;background:#2a7;color:#fff;',
        'border:none;font-size:1.05em;border-radius:4px;cursor:pointer}',
        '.pair-btn{background:#ddd;border:1px solid #aaa;border-radius:3px;',
        'padding:3px 8px;cursor:pointer;font-size:0.95em}',
        '.note{font-size:0.82em;color:#666;margin-top:6px}',
        'hr{margin:20px 0;border:none;border-top:1px solid #ddd}',
        '</style></head><body>',
        '<h1>Enigma Config</h1>',
        ip_line,

        # ── Section 1: Plugboard (separate forms, no nesting issue) ───────────
        '<h2>Plugboard</h2>',
        '<div style="margin-bottom:6px">',
        ''.join(pairs_html),
        '</div>',
        # Add-pair form
        '<form method="post" style="margin-top:8px">',
        '<input type="hidden" name="action" value="add_plug">',
        '<label style="display:block;margin-bottom:4px">',
        'Add pair &ndash; two letters (e.g. <code>AM</code>):',
        '</label>',
        '<input type="text" name="plug" maxlength="2" size="5" '
        'style="font-size:1.1em;text-transform:uppercase">',
        ' <button type="submit" style="padding:4px 10px">Add pair</button>',
        '</form>',
        '<p class="note">Conflicting or duplicate pairs are resolved '
        'automatically by the plugboard logic on next boot.</p>',

        '<hr>',

        # ── Section 2: Main settings form (Apply & Reboot) ───────────────────
        '<form method="post">',
        '<input type="hidden" name="action" value="apply">',

        '<h2>Rotors &amp; Start Positions</h2>',
        '<table>',
        '<tr>',
        '<th></th>',
        '<th>Left rotor</th>',
        '<th>Middle rotor</th>',
        '<th>Right rotor<br><small>(fast)</small></th>',
        '</tr>',
        '<tr>',
        '<th style="text-align:right">Rotor</th>',
        '<td>', _select('rotor1', _ROTOR_NAMES, r[0] if len(r) > 0 else 'I'),   '</td>',
        '<td>', _select('rotor2', _ROTOR_NAMES, r[1] if len(r) > 1 else 'II'),  '</td>',
        '<td>', _select('rotor3', _ROTOR_NAMES, r[2] if len(r) > 2 else 'III'), '</td>',
        '</tr>',
        '<tr>',
        '<th style="text-align:right">Start pos.</th>',
        '<td>', _select('pos1', _LETTERS, p[0] if len(p) > 0 else 'A'), '</td>',
        '<td>', _select('pos2', _LETTERS, p[1] if len(p) > 1 else 'A'), '</td>',
        '<td>', _select('pos3', _LETTERS, p[2] if len(p) > 2 else 'A'), '</td>',
        '</tr>',
        '</table>',

        '<h2>Reflector</h2>',
        _select('reflector', _REFLECTOR_NAMES, reflector),

        '<p class="note">The current plugboard pairs (shown above) are '
        'included automatically when you apply.</p>',

        '<br>',
        '<button class="apply-btn" type="submit">Apply &amp; Reboot</button>',
        '<p class="note">Saves all settings to <code>settings.json</code> on '
        'the Pico W filesystem and reboots the device. Changes take effect '
        'after the reboot.</p>',

        '</form>',
        '</body></html>',
    ]
    return ''.join(parts)


# HTTP helpers

def _http_response(status, body, extra_headers=""):
    """Return a complete HTTP/1.0 response as bytes."""
    body_bytes = body.encode('utf-8')
    header = (
        "HTTP/1.0 {}\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Content-Length: {}\r\n"
        "{}"
        "\r\n"
    ).format(status, len(body_bytes), extra_headers)
    return header.encode('utf-8') + body_bytes


def _redirect(location="/"):
    """Return a 302 redirect response as bytes."""
    return _http_response(
        "302 Found",
        '<html><body>Redirecting&hellip; <a href="{}">click here</a>'
        '</body></html>'.format(location),
        extra_headers="Location: {}\r\n".format(location),
    )


# Request handler

def _handle_request(raw, settings, ip=""):
    """Parse one HTTP request and return (response_bytes, do_reboot)."""
    try:
        if b'\r\n\r\n' in raw:
            header_part, body_bytes = raw.split(b'\r\n\r\n', 1)
        else:
            header_part, body_bytes = raw, b''
        try:
            header_text = header_part.decode('utf-8')
        except Exception:
            header_text = ''
        first_line = header_text.split('\r\n')[0]
        parts  = first_line.split(' ')
        method = parts[0] if parts else 'GET'
        path   = parts[1] if len(parts) > 1 else '/'
        try:
            body = body_bytes.decode('utf-8')
        except Exception:
            body = ''
    except Exception:
        return _http_response("400 Bad Request",
                              "<html><body>Bad request</body></html>"), False

    # Serve main page
    if method == 'GET':
        if path == '/favicon.ico':
            return _http_response("404 Not Found", ""), False
        return _http_response("200 OK", _build_page(settings, ip)), False

    if method == 'POST':
        params = _parse_form(body)
        action = params.get("action", "")

        # Apply all settings => save + reboot
        if action == "apply":
            # rotors
            for i, key in enumerate(("rotor1", "rotor2", "rotor3")):
                val = params.get(key, "")
                if val in ROTOR_WIRINGS:
                    settings["rotors"][i] = val
            # positions
            for i, key in enumerate(("pos1", "pos2", "pos3")):
                val = params.get(key, "").upper()
                if len(val) == 1 and 'A' <= val <= 'Z':
                    settings["positions"][i] = val
            # reflector
            refl = params.get("reflector", "")
            if refl in REFLECTOR_WIRINGS:
                settings["reflector"] = refl

            save_settings(settings)
            body_html = (
                "<!DOCTYPE html><html><head><title>Rebooting\u2026</title>"
                "<meta http-equiv='refresh' content='8;url=/'>"
                "</head><body>"
                "<h2>&#10003; Settings saved &ndash; rebooting&hellip;</h2>"
                "<p>The device is restarting. This page will try to reload "
                "in 8&nbsp;seconds.</p>"
                "<p>If it does not reload, navigate to the device&rsquo;s "
                "IP address manually.</p>"
                "</body></html>"
            )
            return _http_response("200 OK", body_html), True  # signal reboot

        # Add plugboard pair
        elif action == "add_plug":
            plug = params.get("plug", "").upper().strip()
            if (len(plug) == 2
                    and plug[0].isalpha() and plug[1].isalpha()
                    and plug[0] != plug[1]):
                c1, c2 = plug[0], plug[1]
                # Remove conflicting pairs
                settings["plugboard"] = [
                    pr for pr in settings["plugboard"]
                    if isinstance(pr, (list, tuple)) and len(pr) == 2
                    and pr[0] != c1 and pr[1] != c1
                    and pr[0] != c2 and pr[1] != c2
                ]
                settings["plugboard"].append([c1, c2])
                save_settings(settings)
            return _redirect(), False

        # Remove plugboard pair
        elif action == "remove_plug":
            plug = params.get("plug", "").upper().strip()
            if len(plug) == 2:
                target = {plug[0], plug[1]}
                settings["plugboard"] = [
                    pr for pr in settings["plugboard"]
                    if not (isinstance(pr, (list, tuple))
                            and len(pr) == 2
                            and {str(pr[0]).upper(), str(pr[1]).upper()} == target)
                ]
                save_settings(settings)
            return _redirect(), False

    # fallback
    return _http_response("404 Not Found",
                          "<html><body>Not found</body></html>"), False


# WiFi connection

def connect_wifi():
    """Connect to station Wi-Fi (STA mode only).

    Returns the IP address string if connected, or an empty string if the
    connection failed or no credentials are configured.
    Prints progress messages to the USB serial console.
    """
    import network
    from wifi_config import WIFI_SSID, WIFI_PASSWORD

    if not WIFI_SSID:
        print("Wi-Fi: no SSID configured in wifi_config.py; web UI unavailable.")
        return ""

    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        print("Connecting to Wi-Fi '{}'...".format(WIFI_SSID))
        sta.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(20):
            if sta.isconnected():
                break
            time.sleep(0.5)
    if sta.isconnected():
        ip = sta.ifconfig()[0]
        print("Wi-Fi connected – IP: {}".format(ip))
        return ip
    print("Wi-Fi connection failed; web UI unavailable.")
    sta.active(False)
    return ""


# ── Main server loop (runs in a background thread) ────────────────────────────

def run_web_server(settings, ip=""):
    """Blocking HTTP server loop – intended to run via _thread.start_new_thread.

    Handles one request at a time.  On "Apply & Reboot", sends the response
    then calls machine.reset() after a short delay.
    """
    try:
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(addr)
        srv.listen(2)
        print("HTTP server listening on :80")
    except Exception as e:
        print("Web server failed to start:", e)
        return

    while True:
        try:
            conn, _client = srv.accept()
            conn.settimeout(5.0)
            try:
                # Full HTTP request (headers + body)
                raw = b''
                while True:
                    chunk = conn.recv(512)
                    if not chunk:
                        break
                    raw += chunk
                    # stop when received full request
                    if b'\r\n\r\n' in raw:
                        hdr_end = raw.index(b'\r\n\r\n') + 4
                        hdr_text = raw[:hdr_end].decode('utf-8', 'ignore')
                        content_length = 0
                        for line in hdr_text.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                try:
                                    content_length = int(
                                        line.split(':', 1)[1].strip()
                                    )
                                except ValueError:
                                    pass
                        if len(raw) - hdr_end >= content_length:
                            break

                response, do_reboot = _handle_request(raw, settings, ip)
                conn.sendall(response)
            except Exception as ex:
                print("Web server request error:", ex)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

            if do_reboot:
                time.sleep(1)
                machine.reset()

        except Exception as ex:
            print("Web server accept error:", ex)
            time.sleep(0.1)
