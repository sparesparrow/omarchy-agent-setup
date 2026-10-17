#!/usr/bin/env python3
"""Terminal console for MIA's voice state machine (/ws/voice).

Sends only the commands MIA lets a console send (wake, go now, cancel, yes, no, end dictation,
verbosity) and shows the state, LED and tone cue, what MIA said and what it heard.

MIA's /ws/voice currently drives a simulated machine inside the API process, not the live
voice router. Pressing a key here does not control the car.

Configuration comes from the environment or flags, never from the command line for secrets:
  MIA_REPO       path to your own checkout of sparesparrow/mia (its codec is imported)
  MIA_VOICE_URL  ws:// or wss:// URL, for example ws://mia.local:8000/ws/voice
  --key-env      name of the variable that holds the X-API-Key value (default MIA_API_KEY)

Orchestrator mode (no terminal needed):
  --state            print one JSON status object and exit
  --command NAME     send exactly one whitelisted command and print JSON
  --confirm yes      required before Confirm; refuses anything else
  --verbosity LEVEL  required for set-verbosity: quiet, normal or chatty

Commands: wake, go-now, cancel, yes, no, end-dictation, set-verbosity.
The command is checked against the machine state before it is sent; an unknown
state refuses every command except cancel.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import ipaddress
import os
import re
import secrets
import select
import socket
import ssl
import struct
import sys
import time
import uuid
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_MESSAGE = 1 << 20
HANDSHAKE_LIMIT = 16384
TAILSCALE = ipaddress.ip_network("100.64.0.0/10")
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
ALLOWED_COMMANDS = frozenset(
    {"Wake", "GoNow", "Cancel", "Confirm", "Deny", "EndDictation", "SetVerbosity"}
)
COMMAND_NAMES = {
    "wake": "Wake",
    "go-now": "GoNow",
    "cancel": "Cancel",
    "yes": "Confirm",
    "no": "Deny",
    "end-dictation": "EndDictation",
    "set-verbosity": "SetVerbosity",
}
VERBOSITY_NAMES = {"quiet": "QUIET", "normal": "NORMAL", "chatty": "CHATTY"}
# Where each command is meaningful. Cancel is always allowed; an unknown state
# refuses everything else (fail closed).
COMMAND_STATES = {
    "Wake": {"idle"},
    "GoNow": {"window", "speaking"},
    "Confirm": {"confirming"},
    "Deny": {"confirming", "window"},
    "EndDictation": {"dictating"},
    "SetVerbosity": {"idle", "listening", "executing", "window", "confirming", "speaking", "dictating", "warning"},
}
CODEC_PATH = Path("apps/rpi-backend/py-api")


class ConsoleError(Exception):
    pass


class ConsoleClosed(ConsoleError):
    pass


def clean(value, limit=100):
    text = CONTROL.sub("?", str(value))
    return text if len(text) <= limit else text[: limit - 1] + "~"


def address_is_trusted(address):
    ip = ipaddress.ip_address(address)
    return ip.is_loopback or ip.is_private or ip.is_link_local or ip in TAILSCALE


def parse_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ("ws", "wss"):
        raise ConsoleError("URL must start with ws:// or wss://")
    if not parts.hostname:
        raise ConsoleError("URL has no host")
    if parts.username or parts.password:
        raise ConsoleError("Do not put credentials in the URL")
    if parts.query or parts.fragment:
        raise ConsoleError("URL must not contain a query or fragment")
    try:
        port = parts.port or (443 if parts.scheme == "wss" else 80)
    except ValueError:
        raise ConsoleError("URL has an invalid port") from None
    path = parts.path or "/ws/voice"
    if CONTROL.search(path) or " " in path:
        raise ConsoleError("URL path contains forbidden characters")
    return parts.scheme, parts.hostname, port, path


def check_transport(scheme, infos):
    if scheme == "wss":
        return
    for info in infos:
        if not address_is_trusted(info[4][0].split("%")[0]):
            raise ConsoleError(
                "Refusing plain ws:// to a public address: the API key would travel unencrypted. "
                "Use wss://, or a private or Tailscale address."
            )


class WebSocket:
    def __init__(self, sock, leftover=b""):
        self.sock = sock
        self.buffer = bytearray(leftover)
        self.fragments = bytearray()
        self.in_message = False

    @classmethod
    def connect(cls, url, api_key=None, timeout=10.0):
        scheme, host, port, path = parse_url(url)
        if api_key is not None and (not api_key.strip() or CONTROL.search(api_key)):
            raise ConsoleError("API key is empty or contains control characters")
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror as error:
            raise ConsoleError(f"Cannot resolve {clean(host)}: {error}") from None
        check_transport(scheme, infos)
        family, kind, proto, _, address = infos[0]
        sock = socket.socket(family, kind, proto)
        sock.settimeout(timeout)
        try:
            sock.connect(address)
            if scheme == "wss":
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
            key = base64.b64encode(secrets.token_bytes(16)).decode()
            default_port = 443 if scheme == "wss" else 80
            shown_host = f"[{host}]" if ":" in host else host
            host_header = shown_host if port == default_port else f"{shown_host}:{port}"
            lines = [
                f"GET {path} HTTP/1.1",
                f"Host: {host_header}",
                "Upgrade: websocket",
                "Connection: Upgrade",
                f"Sec-WebSocket-Key: {key}",
                "Sec-WebSocket-Version: 13",
            ]
            if api_key:
                lines.append(f"X-API-Key: {api_key}")
            sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode("ascii"))
            raw = bytearray()
            while b"\r\n\r\n" not in raw:
                chunk = sock.recv(4096)
                if not chunk:
                    raise ConsoleError("Server closed the connection during the handshake")
                raw += chunk
                if len(raw) > HANDSHAKE_LIMIT:
                    raise ConsoleError("Handshake response is too large")
            head, _, rest = bytes(raw).partition(b"\r\n\r\n")
            status_line, *header_lines = head.decode("latin-1").split("\r\n")
            code = status_line.split(" ", 2)[1] if status_line.count(" ") >= 1 else "?"
            if code != "101":
                hint = " (wrong or missing API key, or VOICE_CONSOLE=1 is not set on the Pi)" if code in ("401", "403") else ""
                raise ConsoleError(f"Server refused the connection: HTTP {clean(code, 8)}{hint}")
            headers = {}
            for line in header_lines:
                name, _, value = line.partition(":")
                headers[name.strip().lower()] = value.strip()
            expected = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
            if headers.get("sec-websocket-accept") != expected:
                raise ConsoleError("Server did not complete the WebSocket handshake correctly")
            sock.settimeout(timeout)
            return cls(sock, rest)
        except (OSError, ssl.SSLError) as error:
            sock.close()
            raise ConsoleError(f"Connection failed: {clean(error)}") from None
        except ConsoleError:
            sock.close()
            raise

    def _send_frame(self, opcode, payload=b""):
        size = len(payload)
        if size < 126:
            header = bytes([0x80 | opcode, 0x80 | size])
        elif size < 65536:
            header = bytes([0x80 | opcode, 0x80 | 126]) + struct.pack(">H", size)
        else:
            header = bytes([0x80 | opcode, 0x80 | 127]) + struct.pack(">Q", size)
        mask = secrets.token_bytes(4)
        body = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(header + mask + body)

    def send_binary(self, data):
        if len(data) > MAX_MESSAGE:
            raise ConsoleError("Message is too large")
        self._send_frame(0x2, data)

    def close(self):
        try:
            self._send_frame(0x8, struct.pack(">H", 1000))
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass

    def _next_frame(self):
        buf = self.buffer
        if len(buf) < 2:
            return None
        first, second = buf[0], buf[1]
        if first & 0x70:
            raise ConsoleError("Server used an unsupported WebSocket extension")
        if second & 0x80:
            raise ConsoleError("Server sent a masked frame")
        length, position = second & 0x7F, 2
        if length == 126:
            if len(buf) < 4:
                return None
            length, position = struct.unpack(">H", bytes(buf[2:4]))[0], 4
        elif length == 127:
            if len(buf) < 10:
                return None
            length, position = struct.unpack(">Q", bytes(buf[2:10]))[0], 10
        if length > MAX_MESSAGE:
            raise ConsoleError("Server sent a frame that is too large")
        if len(buf) < position + length:
            return None
        payload = bytes(buf[position : position + length])
        del buf[: position + length]
        return bool(first & 0x80), first & 0x0F, payload

    def _messages(self):
        out = []
        while True:
            frame = self._next_frame()
            if frame is None:
                return out
            fin, opcode, payload = frame
            if opcode >= 0x8:
                if not fin or len(payload) > 125:
                    raise ConsoleError("Server sent an invalid control frame")
                if opcode == 0x8:
                    raise ConsoleClosed("Server closed the connection")
                if opcode == 0x9:
                    self._send_frame(0xA, payload)
                continue
            if opcode == 0x1:
                raise ConsoleError("Server sent a text frame; envelopes are binary")
            if opcode == 0x2:
                if self.in_message:
                    raise ConsoleError("Server interleaved WebSocket messages")
                self.in_message, self.fragments = True, bytearray()
            elif opcode == 0x0:
                if not self.in_message:
                    raise ConsoleError("Server sent an unexpected continuation frame")
            else:
                raise ConsoleError("Server sent an unknown frame type")
            self.fragments += payload
            if len(self.fragments) > MAX_MESSAGE:
                raise ConsoleError("Server sent a message that is too large")
            if fin:
                out.append(bytes(self.fragments))
                self.in_message, self.fragments = False, bytearray()

    def poll(self, timeout=0.0):
        ready, _, _ = select.select([self.sock], [], [], timeout)
        if ready:
            try:
                chunk = self.sock.recv(65536)
                while hasattr(self.sock, "pending") and self.sock.pending():
                    chunk += self.sock.recv(self.sock.pending())
            except (OSError, ssl.SSLError) as error:
                raise ConsoleClosed(f"Connection lost: {clean(error)}") from None
            if not chunk:
                raise ConsoleClosed("Server closed the connection")
            self.buffer += chunk
        return self._messages()


def build_keymap(types):
    source = types.Source.CONSOLE
    verbosity = types.Verbosity
    return {
        "w": ("wake", types.Wake(source)),
        "g": ("go now", types.GoNow(source)),
        "c": ("cancel", types.Cancel(source)),
        "y": ("yes", types.Confirm(source)),
        "n": ("no", types.Deny(source)),
        "e": ("end dictation", types.EndDictation(source)),
        "1": ("quiet", types.SetVerbosity(verbosity.QUIET, source)),
        "2": ("normal", types.SetVerbosity(verbosity.NORMAL, source)),
        "3": ("chatty", types.SetVerbosity(verbosity.CHATTY, source)),
    }


def _value(item):
    return getattr(item, "value", item)


class Console:
    def __init__(self, ws, bundle):
        self.ws = ws
        self.codec = bundle.codec
        self.messages = bundle.messages
        self.keymap = build_keymap(bundle.types)
        self.session = uuid.uuid4().hex
        self.seq = 0
        self.state, self.led, self.tone = "unknown", "-", "-"
        self.said, self.heard = "", ""
        self.log = deque(maxlen=6)

    def _send(self, envelope):
        self.ws.send_binary(self.codec.encode_envelope(envelope))

    def _envelope(self, op, payload=b""):
        m = self.messages
        self.seq += 1
        return m.Envelope(
            service=m.Service.VOICE, session_id=self.session, op=op, seq=self.seq, payload=payload
        )

    def open_session(self, timeout=5.0):
        m = self.messages
        self._send(self._envelope(m.Op.OPEN))
        wanted = self.seq
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for data in self.ws.poll(0.2):
                envelope = self.codec.decode_envelope(data)
                if envelope.op == m.Op.OPEN and envelope.seq == wanted and not envelope.payload:
                    if envelope.status != m.Status.OK:
                        raise ConsoleError(f"Server refused the session: {m.Status(envelope.status).name}")
                    return
                self.apply(envelope)
        raise ConsoleError("No answer to the session request")

    def close_session(self):
        try:
            self._send(self._envelope(self.messages.Op.CLOSE))
        except (OSError, ConsoleError):
            pass
        self.ws.close()

    def send_key(self, key):
        entry = self.keymap.get(key)
        if entry is None:
            return False
        label, command = entry
        if type(command).__name__ not in ALLOWED_COMMANDS:
            raise ConsoleError("Blocked: this command is not permitted from a console")
        payload = self.codec.encode_command(command)
        self._send(self._envelope(self.messages.Op.DATA, payload))
        self.log.append(f"sent: {label}")
        return True

    def send_command(self, name, verbosity=None, confirmed=False):
        """Send exactly one whitelisted command, gated by the current state."""
        if name not in COMMAND_NAMES:
            raise ConsoleError(f"Unknown command: {clean(name, 40)}")
        command_name = COMMAND_NAMES[name]
        if command_name not in ALLOWED_COMMANDS:
            raise ConsoleError("Blocked: this command is not permitted from a console")
        if command_name != "Cancel" and self.state not in COMMAND_STATES[command_name]:
            raise ConsoleError(
                f"Blocked: {command_name} is not allowed in state {clean(self.state, 30)}"
            )
        if command_name == "Confirm" and confirmed is not True:
            raise ConsoleError("Blocked: Confirm requires --confirm yes")
        if command_name == "SetVerbosity":
            if verbosity not in VERBOSITY_NAMES:
                raise ConsoleError("Blocked: set-verbosity requires --verbosity quiet, normal or chatty")
            command = self.keymap[{"QUIET": "1", "NORMAL": "2", "CHATTY": "3"}[VERBOSITY_NAMES[verbosity]]][1]
        else:
            key = {"Wake": "w", "GoNow": "g", "Cancel": "c", "Confirm": "y", "Deny": "n", "EndDictation": "e"}[command_name]
            command = self.keymap[key][1]
        before = self.state
        payload = self.codec.encode_command(command)
        self._send(self._envelope(self.messages.Op.DATA, payload))
        self.log.append(f"sent: {name}")
        return {"command": command_name, "sent": True, "state_before": before}

    def status(self):
        return {
            "state": self.state,
            "led": self.led,
            "tone": self.tone,
            "said": self.said,
            "heard": self.heard,
            "simulated": True,
        }

    def apply(self, envelope):
        m = self.messages
        if not envelope.payload:
            if envelope.status != m.Status.OK:
                self.log.append(f"server: {m.Status(envelope.status).name}")
            return
        try:
            event = self.codec.decode_event(envelope.payload)
        except self.codec.CodecError:
            self.log.append("received an unreadable event")
            return
        name = type(event).__name__
        if name == "StateChanged":
            self.state = clean(_value(event.current))
        elif name == "Feedback":
            self.led, self.tone = clean(event.led), clean(event.tone)
            self.log.append(f"cue: {clean(_value(event.state))}")
        elif name == "Speak":
            self.said = clean(event.phrase)
        elif name == "Transcript":
            self.heard = clean(event.text)

    def handle(self, data):
        try:
            self.apply(self.codec.decode_envelope(data))
        except self.codec.CodecError:
            self.log.append("received an unreadable message")

    def render(self):
        lines = [
            "MIA voice console  -  SIMULATED machine, does not control the car",
            "",
            f"State:     {self.state}",
            f"LED/tone:  {self.led} / {self.tone}",
            f"MIA said:  {self.said}",
            f"Heard:     {self.heard}",
            "",
            *[f"  {line}" for line in self.log],
            "",
            "w wake   g go now   c cancel   y yes   n no   e end dictation",
            "1 quiet  2 normal   3 chatty    q quit   (cancel never needs speech)",
        ]
        return "\x1b[2J\x1b[H" + "\n".join(lines) + "\n"


def load_codec(repo):
    base = Path(repo).expanduser().resolve() / CODEC_PATH
    if not (base / "services/voice_fsm/wire/codec.py").is_file():
        raise ConsoleError(f"{clean(repo)} is not a MIA checkout (voice codec not found)")
    try:
        import flatbuffers  # noqa: F401
    except ImportError:
        raise ConsoleError(
            "The Python package flatbuffers is missing. Install it with your package manager, "
            "for example pacman -Ss flatbuffers."
        ) from None
    sys.path.insert(0, str(base))
    try:
        from services.voice_fsm import types
        from services.voice_fsm.wire import codec, messages
    except ImportError as error:
        raise ConsoleError(f"Cannot import MIA's voice codec: {clean(error)}") from None
    return SimpleNamespace(types=types, codec=codec, messages=messages)


def run_terminal(console):
    import termios
    import tty

    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        while True:
            sys.stdout.write(console.render())
            sys.stdout.flush()
            ready, _, _ = select.select([fd, console.ws.sock], [], [], 0.25)
            if fd in ready:
                key = os.read(fd, 1).decode("latin-1")
                if key in ("q", "\x03", "\x04"):
                    return
                console.send_key(key)
            for data in console.ws.poll(0):
                console.handle(data)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        sys.stdout.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=os.environ.get("MIA_VOICE_URL"))
    parser.add_argument("--repo", default=os.environ.get("MIA_REPO"))
    parser.add_argument("--key-env", default="MIA_API_KEY")
    parser.add_argument("--state", action="store_true", help="print JSON status and exit")
    parser.add_argument("--command", choices=sorted(COMMAND_NAMES), help="send one whitelisted command")
    parser.add_argument("--confirm", choices=["yes"], help="required before --command yes")
    parser.add_argument("--verbosity", choices=sorted(VERBOSITY_NAMES), help="required for --command set-verbosity")
    parser.add_argument("--wait", type=float, default=1.0, help="seconds to wait for events in non-interactive mode")
    args = parser.parse_args(argv)
    try:
        if args.command and args.state:
            raise ConsoleError("Use either --state or --command, not both")
        if args.confirm and args.command != "yes":
            raise ConsoleError("--confirm is only valid with --command yes")
        if args.verbosity and args.command != "set-verbosity":
            raise ConsoleError("--verbosity is only valid with --command set-verbosity")
        if not args.url or not args.repo:
            raise ConsoleError("Set MIA_VOICE_URL and MIA_REPO (or pass --url and --repo)")
        if not ENV_NAME.fullmatch(args.key_env):
            raise ConsoleError("--key-env must be the NAME of an environment variable")
        parse_url(args.url)
        non_interactive = bool(args.state or args.command)
        if not non_interactive and not (sys.stdin.isatty() and sys.stdout.isatty()):
            raise ConsoleError("The console needs an interactive terminal")
        bundle = load_codec(args.repo)
        ws = WebSocket.connect(args.url, os.environ.get(args.key_env) or None)
        console = Console(ws, bundle)
        try:
            console.open_session()
            if non_interactive:
                for data in console.ws.poll(max(0.0, args.wait)):
                    console.handle(data)
                if args.state:
                    print(json.dumps(console.status(), ensure_ascii=False))
                    return 0
                result = console.send_command(
                    args.command, verbosity=args.verbosity, confirmed=args.confirm == "yes"
                )
                for data in console.ws.poll(max(0.0, args.wait)):
                    console.handle(data)
                result["state_after"] = console.state
                print(json.dumps(result, ensure_ascii=False))
                return 0
            run_terminal(console)
        finally:
            console.close_session()
        return 0
    except ConsoleClosed as error:
        sys.stderr.write(f"Disconnected: {error}\n")
        return 1
    except ConsoleError as error:
        sys.stderr.write(f"BLOCKED: {error}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
