import base64
import enum
import hashlib
import importlib.util
import io
import json
import os
import socket
import struct
import threading
import unittest
from contextlib import redirect_stderr
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "setup/mia-voice-console.py"
SPEC = importlib.util.spec_from_file_location("mia_voice_console", SOURCE)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


# ---- stand-in for MIA's codec (the real one needs flatbuffers and a MIA checkout) ----
class Source(str, enum.Enum):
    CONSOLE = "console"


class Verbosity(str, enum.Enum):
    QUIET = "quiet"
    NORMAL = "normal"
    CHATTY = "chatty"


class State(str, enum.Enum):
    IDLE = "idle"
    WINDOW = "window"


class Wake: 
    def __init__(self, source): self.source = source
class GoNow(Wake): pass
class Cancel(Wake): pass
class Confirm(Wake): pass
class Deny(Wake): pass
class EndDictation(Wake): pass
class SetVerbosity:
    def __init__(self, level, source): self.level, self.source = level, source
class StateChanged:
    def __init__(self, previous, current): self.previous, self.current = previous, current
class Feedback:
    def __init__(self, state, led, tone): self.state, self.led, self.tone = state, led, tone
class Speak:
    def __init__(self, phrase): self.phrase = phrase
class Transcript:
    def __init__(self, text): self.text = text


class Service(enum.IntEnum):
    UNKNOWN = 0
    VOICE = 1


class Op(enum.IntEnum):
    DATA = 0
    OPEN = 1
    CLOSE = 2


class Status(enum.IntEnum):
    OK = 0
    NOT_PERMITTED = 4


@dataclass(frozen=True)
class Envelope:
    service: int = Service.VOICE
    session_id: str = ""
    op: int = Op.DATA
    status: int = Status.OK
    seq: int = 0
    payload: bytes = b""
    version: int = 1


class CodecError(ValueError):
    pass


EVENTS = {"StateChanged": StateChanged, "Feedback": Feedback, "Speak": Speak, "Transcript": Transcript}


def encode_command(cmd):
    return json.dumps({"cmd": type(cmd).__name__}).encode()


def encode_envelope(env):
    return json.dumps({**env.__dict__, "payload": env.payload.hex()}).encode()


def decode_envelope(data):
    try:
        raw = json.loads(data)
        raw["payload"] = bytes.fromhex(raw["payload"])
        return Envelope(**raw)
    except (ValueError, KeyError, TypeError) as error:
        raise CodecError(str(error)) from None


def decode_event(payload):
    try:
        raw = json.loads(payload)
        return EVENTS[raw["event"]](*raw["args"])
    except (ValueError, KeyError, TypeError) as error:
        raise CodecError(str(error)) from None


def event_payload(name, *args):
    return json.dumps({"event": name, "args": list(args)}).encode()


BUNDLE = SimpleNamespace(
    types=SimpleNamespace(
        Source=Source, Verbosity=Verbosity, Wake=Wake, GoNow=GoNow, Cancel=Cancel, Confirm=Confirm,
        Deny=Deny, EndDictation=EndDictation, SetVerbosity=SetVerbosity,
    ),
    codec=SimpleNamespace(
        encode_command=encode_command, encode_envelope=encode_envelope,
        decode_envelope=decode_envelope, decode_event=decode_event, CodecError=CodecError,
    ),
    messages=SimpleNamespace(Envelope=Envelope, Service=Service, Op=Op, Status=Status),
)


class FakeWS:
    def __init__(self):
        self.sent, self.incoming, self.closed = [], [], False

    def send_binary(self, data):
        self.sent.append(data)

    def poll(self, timeout=0.0):
        out, self.incoming = self.incoming, []
        return out

    def close(self):
        self.closed = True


# ---- tiny WebSocket server on loopback ----
def frame(opcode, payload=b"", fin=True):
    first = (0x80 if fin else 0) | opcode
    n = len(payload)
    if n < 126:
        return bytes([first, n]) + payload
    if n < 65536:
        return bytes([first, 126]) + struct.pack(">H", n) + payload
    return bytes([first, 127]) + struct.pack(">Q", n) + payload


def read_exact(conn, n):
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise EOFError
        data += chunk
    return data


def read_client_frame(conn):
    first, second = read_exact(conn, 2)
    length = second & 0x7F
    if length == 126:
        length = struct.unpack(">H", read_exact(conn, 2))[0]
    elif length == 127:
        length = struct.unpack(">Q", read_exact(conn, 8))[0]
    masked = bool(second & 0x80)
    mask = read_exact(conn, 4) if masked else b"\0\0\0\0"
    body = bytes(b ^ mask[i % 4] for i, b in enumerate(read_exact(conn, length)))
    return first & 0x0F, masked, body


class Server:
    def __init__(self, script, status="101 Switching Protocols", bad_accept=False):
        self.script, self.status, self.bad_accept = script, status, bad_accept
        self.headers, self.results = {}, {}
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.thread = threading.Thread(target=self.serve, daemon=True)
        self.thread.start()

    def serve(self):
        conn, _ = self.listener.accept()
        with conn:
            raw = b""
            while b"\r\n\r\n" not in raw:
                raw += conn.recv(4096)
            lines = raw.decode().split("\r\n")
            self.request_line = lines[0]
            self.headers = {l.split(":", 1)[0].lower(): l.split(":", 1)[1].strip() for l in lines[1:] if ":" in l}
            if not self.status.startswith("101"):
                conn.sendall(f"HTTP/1.1 {self.status}\r\nContent-Length: 0\r\n\r\n".encode())
                return
            accept = base64.b64encode(hashlib.sha1((self.headers["sec-websocket-key"] + GUID).encode()).digest()).decode()
            if self.bad_accept:
                accept = "wrong"
            conn.sendall(f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n".encode())
            self.script(conn, self)

    def url(self, path="/ws/voice"):
        return f"ws://127.0.0.1:{self.port}{path}"

    def close(self):
        self.listener.close()


def collect(ws, count, attempts=60):
    out = []
    for _ in range(attempts):
        out += ws.poll(0.1)
        if len(out) >= count:
            break
    return out


class AddressRules(unittest.TestCase):
    def test_trusted_and_public_addresses(self):
        for address in ("127.0.0.1", "10.1.2.3", "192.168.1.5", "100.64.0.1", "100.127.255.254", "::1", "fc00::1"):
            with self.subTest(address=address):
                self.assertTrue(MOD.address_is_trusted(address))
        for address in ("8.8.8.8", "100.128.0.1", "2001:4860:4860::8888"):
            with self.subTest(address=address):
                self.assertFalse(MOD.address_is_trusted(address))

    def test_plain_ws_to_public_address_is_refused_but_wss_is_not(self):
        public = [(2, 1, 6, "", ("8.8.8.8", 80))]
        with self.assertRaises(MOD.ConsoleError):
            MOD.check_transport("ws", public)
        MOD.check_transport("wss", public)
        MOD.check_transport("ws", [(2, 1, 6, "", ("100.64.1.1", 80))])

    def test_url_rules(self):
        self.assertEqual(MOD.parse_url("ws://mia.local:8000/ws/voice"), ("ws", "mia.local", 8000, "/ws/voice"))
        self.assertEqual(MOD.parse_url("wss://host")[2:], (443, "/ws/voice"))
        for bad in ("http://host/x", "ws://user:pw@host/x", "ws://host/x?key=1", "ws://host:99999/x", "ws:///x", "ws://host/a b"):
            with self.subTest(url=bad):
                with self.assertRaises(MOD.ConsoleError):
                    MOD.parse_url(bad)


class WebSocketClient(unittest.TestCase):
    def test_handshake_sends_key_header_and_masks_frames(self):
        def script(conn, server):
            opcode, masked, body = read_client_frame(conn)
            server.results.update(opcode=opcode, masked=masked, body=body)
            conn.sendall(frame(0x2, b"small"))
            conn.sendall(frame(0x2, b"frag-", fin=False) + frame(0x0, b"mented"))
            conn.sendall(frame(0x9, b"hi"))
            conn.sendall(frame(0x2, b"x" * 300))
            conn.sendall(frame(0x2, b"y" * 70000))
            server.results["pong"] = read_client_frame(conn)
            conn.sendall(frame(0x8, struct.pack(">H", 1000)))

        server = Server(script)
        self.addCleanup(server.close)
        ws = MOD.WebSocket.connect(server.url(), "secret-key")
        self.addCleanup(ws.sock.close)
        ws.send_binary(b"hello")
        got = collect(ws, 4)
        self.assertEqual(got[0], b"small")
        self.assertEqual(got[1], b"frag-mented")
        self.assertEqual(len(got[2]), 300)
        self.assertEqual(len(got[3]), 70000)
        with self.assertRaises(MOD.ConsoleClosed):
            for _ in range(40):
                ws.poll(0.1)
        server.thread.join(2)
        self.assertEqual(server.headers["x-api-key"], "secret-key")
        self.assertEqual(server.request_line, "GET /ws/voice HTTP/1.1")
        self.assertEqual(server.results["opcode"], 0x2)
        self.assertTrue(server.results["masked"])
        self.assertEqual(server.results["body"], b"hello")
        self.assertEqual(server.results["pong"][0], 0xA)
        self.assertEqual(server.results["pong"][2], b"hi")

    def test_no_key_header_without_a_key(self):
        server = Server(lambda conn, s: None)
        self.addCleanup(server.close)
        MOD.WebSocket.connect(server.url()).close()
        server.thread.join(2)
        self.assertNotIn("x-api-key", server.headers)

    def test_refused_handshake_explains_without_echoing_the_key(self):
        server = Server(None, status="403 Forbidden")
        self.addCleanup(server.close)
        with self.assertRaises(MOD.ConsoleError) as caught:
            MOD.WebSocket.connect(server.url(), "topsecret")
        self.assertIn("403", str(caught.exception))
        self.assertIn("VOICE_CONSOLE", str(caught.exception))
        self.assertNotIn("topsecret", str(caught.exception))

    def test_wrong_accept_header_is_rejected(self):
        server = Server(lambda c, s: None, bad_accept=True)
        self.addCleanup(server.close)
        with self.assertRaises(MOD.ConsoleError):
            MOD.WebSocket.connect(server.url())

    def test_hostile_frames_are_rejected(self):
        cases = {
            "text frame": frame(0x1, b"hi"),
            "oversize": bytes([0x82, 127]) + struct.pack(">Q", 2 << 20),
            "masked server frame": bytes([0x82, 0x81]) + b"\0\0\0\0" + b"x",
            "extension bits": bytes([0xC2, 0x01]) + b"x",
            "stray continuation": frame(0x0, b"x"),
        }
        for name, payload in cases.items():
            with self.subTest(case=name):
                server = Server(lambda conn, s, p=payload: conn.sendall(p))
                self.addCleanup(server.close)
                ws = MOD.WebSocket.connect(server.url())
                self.addCleanup(ws.sock.close)
                with self.assertRaises(MOD.ConsoleError):
                    for _ in range(40):
                        ws.poll(0.1)

    def test_key_with_control_characters_is_rejected_before_connecting(self):
        for bad in ("a\r\nX-Evil: 1", "", "   "):
            with self.subTest(key=repr(bad)):
                with self.assertRaises(MOD.ConsoleError):
                    MOD.WebSocket.connect("ws://127.0.0.1:1/ws/voice", bad)


class ConsoleLogic(unittest.TestCase):
    def setUp(self):
        self.ws = FakeWS()
        self.console = MOD.Console(self.ws, BUNDLE)

    def envelope(self, payload=b"", status=Status.OK, op=Op.DATA, seq=0):
        return encode_envelope(Envelope(session_id=self.console.session, op=op, status=status, seq=seq, payload=payload))

    def test_only_permitted_commands_exist_and_can_be_sent(self):
        names = {type(command).__name__ for _, command in self.console.keymap.values()}
        self.assertEqual(names, {"Wake", "GoNow", "Cancel", "Confirm", "Deny", "EndDictation", "SetVerbosity"})
        self.assertLessEqual(names, MOD.ALLOWED_COMMANDS)
        forbidden = ("SafetyWarning", "IncomingMessage", "Intent", "DictationText", "SpeakingDone", "ExecutionDone")
        source = SOURCE.read_text()
        keymap_text = source[source.index("def build_keymap"):source.index("def _value")]
        for name in forbidden:
            with self.subTest(name=name):
                self.assertNotIn(name, keymap_text)

    def test_keys_send_the_matching_command_in_a_data_envelope(self):
        expected = {"w": "Wake", "g": "GoNow", "c": "Cancel", "y": "Confirm", "n": "Deny", "e": "EndDictation", "1": "SetVerbosity"}
        for key, name in expected.items():
            self.ws.sent.clear()
            self.assertTrue(self.console.send_key(key))
            envelope = decode_envelope(self.ws.sent[0])
            self.assertEqual(envelope.op, Op.DATA)
            self.assertEqual(envelope.session_id, self.console.session)
            self.assertEqual(json.loads(envelope.payload)["cmd"], name)
        before = len(self.ws.sent)
        self.assertFalse(self.console.send_key("x"))
        self.assertEqual(len(self.ws.sent), before)

    def test_a_command_outside_the_whitelist_is_blocked(self):
        class Rogue: pass
        self.console.keymap["z"] = ("rogue", Rogue())
        with self.assertRaises(MOD.ConsoleError):
            self.console.send_key("z")

    def test_open_session_waits_for_ok_and_rejects_refusal(self):
        self.ws.incoming = [self.envelope(op=Op.OPEN, seq=1)]
        self.console.open_session(timeout=1)
        self.assertEqual(decode_envelope(self.ws.sent[0]).op, Op.OPEN)
        other = MOD.Console(FakeWS(), BUNDLE)
        other.ws.incoming = [encode_envelope(Envelope(session_id=other.session, op=Op.OPEN, status=Status.NOT_PERMITTED, seq=1))]
        with self.assertRaises(MOD.ConsoleError):
            other.open_session(timeout=1)

    def test_events_update_the_display_and_control_characters_are_neutralised(self):
        self.console.handle(self.envelope(event_payload("StateChanged", "idle", "window")))
        self.console.handle(self.envelope(event_payload("Feedback", "window", "yellow_countdown", "double_beep")))
        self.console.handle(self.envelope(event_payload("Speak", "say \x1b[2Jhi\x07")))
        self.console.handle(self.envelope(event_payload("Transcript", "heard\x00this")))
        screen = self.console.render()
        self.assertIn("window", screen)
        self.assertIn("yellow_countdown / double_beep", screen)
        self.assertIn("say ?[2Jhi?", screen)
        self.assertIn("heard?this", screen)
        body = screen.split("\x1b[2J\x1b[H", 1)[1]
        self.assertNotIn("\x07", body)
        self.assertNotIn("\x00", body)
        self.assertEqual(body.count("\x1b"), 0)

    def test_state_enum_values_are_shown_by_value(self):
        self.console.apply(Envelope(payload=json.dumps({"event": "StateChanged", "args": ["idle", "window"]}).encode()))
        self.assertEqual(self.console.state, "window")
        self.console.state = "x"
        with mock.patch.object(BUNDLE.codec, "decode_event", return_value=StateChanged(State.IDLE, State.WINDOW)):
            self.console.apply(Envelope(payload=b"{}"))
        self.assertEqual(self.console.state, "window")

    def test_server_status_and_garbage_are_logged_not_raised(self):
        self.console.handle(self.envelope(status=Status.NOT_PERMITTED))
        self.console.handle(b"not json")
        self.console.apply(Envelope(payload=b"not json"))
        self.assertIn("server: NOT_PERMITTED", list(self.console.log))
        self.assertIn("received an unreadable message", list(self.console.log))
        self.assertIn("received an unreadable event", list(self.console.log))

    def test_banner_states_that_the_machine_is_simulated(self):
        self.assertIn("SIMULATED", self.console.render())
        self.assertIn("does not control the car", self.console.render())


class MainEntrypoint(unittest.TestCase):
    def run_main(self, argv, env):
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=False), redirect_stderr(stderr):
            code = MOD.main(argv)
        return code, stderr.getvalue()

    def test_missing_configuration_is_blocked(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MIA_VOICE_URL", None)
            os.environ.pop("MIA_REPO", None)
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(MOD.main([]), 2)
        self.assertIn("BLOCKED", stderr.getvalue())

    def test_key_env_must_be_a_name_and_the_key_is_never_printed(self):
        code, err = self.run_main(["--url", "ws://127.0.0.1:1/x", "--repo", "/nonexistent", "--key-env", "sk-live-123"], {})
        self.assertEqual(code, 2)
        self.assertNotIn("sk-live-123", err.replace("--key-env", ""))
        code, err = self.run_main(["--url", "ftp://x", "--repo", "/r"], {"MIA_API_KEY": "supersecret"})
        self.assertEqual(code, 2)
        self.assertNotIn("supersecret", err)

    def test_non_mia_checkout_is_rejected(self):
        with mock.patch.object(MOD.sys.stdin, "isatty", return_value=True), mock.patch.object(MOD.sys.stdout, "isatty", return_value=True):
            code, err = self.run_main(["--url", "ws://127.0.0.1:1/x", "--repo", "/tmp"], {})
        self.assertEqual(code, 2)
        self.assertIn("not a MIA checkout", err)

    def test_source_has_only_standard_library_imports_at_module_level(self):
        source = SOURCE.read_text()
        header = source.split("CODEC_PATH", 1)[0]
        imports = {line.split()[1].split(".")[0] for line in header.splitlines() if line.startswith(("import ", "from "))}
        self.assertLessEqual(imports, {"__future__", "argparse", "base64", "hashlib", "ipaddress", "os", "re", "secrets", "select", "socket", "ssl", "struct", "sys", "time", "uuid", "collections", "pathlib", "types", "urllib"})


if __name__ == "__main__":
    unittest.main()
