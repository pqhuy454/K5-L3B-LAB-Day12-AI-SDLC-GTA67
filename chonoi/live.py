"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan [--seed N] [--port 8000]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html` và hai API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool}   (trạng thái phím đang giữ)
    POST /restart -> chơi lại buổi hiện tại (cùng seed, cùng scenario/kho)
    POST /next    -> (chỉ trang trí, chế độ "một ngày") buổi sáng đã kết thúc thì mở buổi tối với kho vừa thu
    POST /new-day -> quay về buổi sáng ban đầu
    GET  /assets/<tên ngắn>.png hoặc /assets/<đường dẫn trong thư mục assets/> (chỉ ảnh/âm thanh)

Chuyển cảnh sáng → tối chỉ có ở cửa sổ chơi; headless vẫn là hai tiến trình riêng qua file kho (Contract G).

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
import math
import os
import sys
import threading
import time
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import load_contract
from .errors import BadInput
from .ids import id_key
from .inputs import LiveInputs
from .inventory import read_inventory
from .runner import Session
from .scenario import load_scenario

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.realpath(os.path.join(ROOT_DIR, "assets"))
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
# Tên ngắn cho vài sprite hay dùng (giữ tương thích client cũ / test).
SPRITE_FILES = {
    "diver.png": ("SpearFishing Assets Pack", "Sprites", "Diver-32x32", "Diver 1.png"),
    "fish-linh.png": ("SpearFishing Assets Pack", "Sprites", "Fish3 - 32x16", "Grey.png"),
    "fish-loc.png": ("Nền sông và nhân vật", "PNG", "enemies", "fish-big.png"),
    "seaweed.png": ("SpearFishing Assets Pack", "Sprites", "SeaWeed - 16x32", "Medium.png"),
    "coral.png": ("SpearFishing Assets Pack", "Sprites", "Corals - 16x16", "Corals.png"),
    "sand.png": ("SpearFishing Assets Pack", "Sprites", "Tiles - 16x16", "Sand.png"),
    "bubble.png": ("SpearFishing Assets Pack", "Sprites", "Bubble - 8x8.png"),
    "table.png": ("Restaurant Assets Pack", "Tiles", "RestaurantFixtures", "fooddrink_restaurant_fixtures_table_dining_round_four_01.png"),
    "stove.png": ("Restaurant Assets Pack", "Tiles", "RestaurantFixtures", "fooddrink_restaurant_fixtures_stove_commercial_six_burner_01.png"),
    "lights.png": ("Restaurant Assets Pack", "Tiles", "CafeProps", "fooddrink_cafe_props_string_lights_warm_segment_01.png"),
}
ASSET_TYPES = {".png": "image/png", ".gif": "image/gif", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".svg": "image/svg+xml", ".ogg": "audio/ogg"}
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
RECENT_EVENTS = 40
RECENT_PRESSES = 30
BUTTON_NAME = {"interact": "E", "catch": "Space"}


def describe_press(sim, mode, tuning) -> str:
    """Mô tả ngữ cảnh lúc bấm nút (CHỈ để log/gỡ lỗi; không ảnh hưởng luật)."""
    if mode == "quan":
        r = tuning["quan"]["interact_radius"]
        cands = sorted(((math.dist(sim.pos, o["pos"]), rank, id_key(o["id"]), kind, o)
                        for rank, kind, arr in ((0, "bếp", sim.stoves), (1, "bàn", sim.tables)) for o in arr),
                       key=lambda c: c[:3])
        hand = sim.hand or "trống"
        if not cands:
            return f"không có bếp/bàn · tay {hand}"
        d, _, _, kind, o = cands[0]
        if d > r:
            return f"không có bếp/bàn trong {r} m (gần nhất {kind} {o['id']} cách {d:.2f} m) · tay {hand}"
        if kind == "bếp":
            detail = f"bếp {o.get('state')}" + (f", món {o.get('dish')}" if o.get("dish") else "")
        else:
            cust = next((c for c in sim.customers if c.get("table_id") == o["id"]), None)
            detail = (f"khách {cust['id']} {cust.get('state')} gọi {cust.get('dish_id') or cust.get('dish')}"
                      if cust else "bàn trống")
        return f"mục tiêu {kind} {o['id']} cách {d:.2f} m ({detail}) · tay {hand}"
    at_surface = sim.pos[1] <= tuning["gather"]["surface_depth"]
    return (("mặt nước" if at_surface else f"dưới nước d={sim.pos[1]:.1f}") +
            f" · giỏ {len(sim.hold)}/{tuning['gather']['hold_capacity']}")


def resolve_asset(name: str):
    """URL /assets/<name> -> (đường dẫn file, content-type) hoặc None. Không cho thoát khỏi thư mục assets/."""
    if name in SPRITE_FILES:
        path = os.path.join(ASSETS_DIR, *SPRITE_FILES[name])
    else:
        rel = urllib.parse.unquote(name).replace("\\", "/").lstrip("/")
        path = os.path.realpath(os.path.join(ASSETS_DIR, rel))
        if os.path.commonpath([ASSETS_DIR, path]) != ASSETS_DIR:
            return None
    ctype = ASSET_TYPES.get(os.path.splitext(path)[1].lower())
    if ctype is None or not os.path.isfile(path):
        return None
    return path, ctype


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa.

    Mở bằng --mode gather thì chơi được "một ngày": hết buổi sáng -> /next mở buổi tối với kho vừa thu.
    """

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, input_log=None):
        self._day_args = (mode, tuning, scenario, seed, inventory)
        self._args = self._day_args
        self.mode = mode
        self.tuning = tuning
        self.inventory_out = inventory_out
        self.input_log_path = input_log     # file log nút (tùy chọn), ghi nối tiếp
        self.presses = []                   # log nút gần nhất, gửi kèm /state
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._reset()

    def _reset(self):
        self.mode = self._args[0]
        self.session = Session(*self._args)
        self.inputs = LiveInputs()
        self.events = []
        self._saved = False
        self.error = None

    def _log(self, entry: dict):
        """Ghi một dòng log nút: terminal + bộ đệm cho client (+ file nếu có --input-log)."""
        self.presses.append(entry)
        del self.presses[:-RECENT_PRESSES]
        sys.stderr.write(f"[nút] {entry['text']}\n")
        if self.input_log_path:
            try:
                with open(self.input_log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except OSError as e:
                sys.stderr.write(f"lỗi ghi log nút: {e}\n")

    def _log_press(self, pressed, context, event_names):
        keys = "+".join(BUTTON_NAME[b] for b in pressed)
        if event_names:
            result = "→ " + ", ".join(event_names)
            ok = True
        else:
            result = "→ KHÔNG có sự kiện (nút không có tác dụng)"
            ok = False
        tick = self.session.tick
        self._log({"tick": tick, "mode": self.mode, "keys": keys, "context": context, "events": event_names,
                   "ok": ok, "text": f"t{tick} {self.mode} [{keys}] {context} {result}"})

    def _log_system(self, what: str):
        self._log({"tick": self.session.tick, "mode": self.mode, "keys": "", "context": what, "events": [],
                   "ok": True, "text": f"t{self.session.tick} {self.mode} {what}"})

    def can_continue(self) -> bool:
        return self.mode == "gather" and self.session.done and self.error is None

    def next_phase(self) -> bool:
        """Buổi sáng xong -> buổi tối, kho = giỏ còn lại (ngất thì rỗng). Trả False nếu chưa chuyển được."""
        with self._lock:
            if not self.can_continue():
                return False
            items = self.session.sim.inventory_items()
            _, tuning, _, seed, _ = self._day_args
            self._args = ("quan", tuning, {}, seed, items)
            self._reset()
            self._log_system(f"[Enter] chuyển sang buổi tối, kho {items}")
            return True

    def new_day(self):
        with self._lock:
            self._args = self._day_args
            self._reset()
            self._log_system("[N] ngày mới")

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if s.done:
            return
        inp = self.inputs.advance()
        pressed = [b for b in BUTTON_NAME if inp.pressed(b)]
        context = describe_press(s.sim, self.mode, self.tuning) if pressed else None
        rows = s.step(inp)
        for row in rows:
            self.events.append(row)
        del self.events[:-RECENT_EVENTS]
        if pressed:
            self._log_press(pressed, context, [r["name"] for r in rows])
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out:
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            snap["meta"] = self.tuning[self.mode]
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            snap["can_continue"] = self.can_continue()
            snap["day_mode"] = self._day_args[0]
            snap["presses"] = self.presses[-8:]
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in ("interact", "catch"):
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        with self._lock:
            self.inputs.set(move, **buttons)

    def restart(self):
        with self._lock:
            self._reset()
            self._log_system("[R] chơi lại buổi này")


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu index.html"}')
        elif path.startswith("/assets/"):
            rel = urllib.parse.unquote(path[len("/assets/"):].lstrip("/\\"))
            filepath = os.path.normpath(os.path.join(ASSETS_DIR, rel))
            if filepath.startswith(ASSETS_DIR) and os.path.isfile(filepath):
                ctype = "application/octet-stream"
                if filepath.lower().endswith(".png"):
                    ctype = "image/png"
                elif filepath.lower().endswith(".svg"):
                    ctype = "image/svg+xml"
                elif filepath.lower().endswith(".mp3"):
                    ctype = "audio/mpeg"
                elif filepath.lower().endswith(".json"):
                    ctype = "application/json"
                elif filepath.lower().endswith(".jpg") or filepath.lower().endswith(".jpeg"):
                    ctype = "image/jpeg"
                with open(filepath, "rb") as f:
                    self._send(200, f.read(), ctype)
            else:
                self._send(404, b'{"error":"asset khong ton tai"}')
                return
            try:
                with open(found[0], "rb") as f:
                    self._send(200, f.read(), found[1])
            except OSError:
                self._send(404, b'{"error":"asset khong doc duoc"}')
        else:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_BODY:
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/restart":
                self.game.restart()
            elif path == "/next":
                if not self.game.next_phase():
                    self._send(409, b'{"error":"buoi sang chua ket thuc"}')
                    return
            elif path == "/new-day":
                self.game.new_day()
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter).")
    p.add_argument("--mode", required=True, choices=["gather", "quan"])
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    p.add_argument("--input-log", dest="input_log", help="ghi log từng lần bấm E/Space (JSON lines) vào file này")
    a = p.parse_args(argv)
    try:
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        tuning = load_contract()["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning)
        inventory = read_inventory(a.inventory) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, a.input_log)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    for stream in (sys.stdout, sys.stderr):  # console Windows (cp1252) không in được tiếng Việt
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
