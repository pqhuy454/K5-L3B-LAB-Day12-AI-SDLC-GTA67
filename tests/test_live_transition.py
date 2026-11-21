"""Cửa sổ chơi: chuyển cảnh sáng -> tối (chỉ ở chonoi.live, không ảnh hưởng headless) và phục vụ asset an toàn."""

import json
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.live import LiveGame, LiveServer, resolve_asset


def _post(url):
    req = urllib.request.Request(url, data=b"{}", method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


class LiveTransitionTest(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def _dock(self, game):
        """Cập bến ngay bước đầu với giỏ dựng sẵn."""
        game.session.step(InputState((0.0, 0.0), {"interact": True, "catch": False}, {"interact"}))
        self.assertTrue(game.session.done)
        self.assertEqual(game.session.sim.reason, "docked")

    def test_next_phase_carries_basket_into_quan(self):
        game = LiveGame("gather", self.tuning, {"hold": ["ca_loc", "bong_sung", "bong_sung"]}, 42)
        self.assertFalse(game.next_phase(), "chưa xong buổi sáng thì không được chuyển")
        self._dock(game)
        self.assertTrue(game.can_continue())
        self.assertTrue(game.next_phase())
        self.assertEqual(game.mode, "quan")
        snap = json.loads(game.state_json())
        self.assertEqual(snap["mode"], "quan")
        self.assertEqual(snap["stock"], {"bong_sung": 2, "ca_loc": 1})
        self.assertEqual(snap["tick"], 0)
        self.assertFalse(snap["can_continue"])
        self.assertEqual(snap["day_mode"], "gather")
        game.restart()                       # R ở buổi tối: chơi lại tối với cùng kho
        self.assertEqual(json.loads(game.state_json())["stock"], {"bong_sung": 2, "ca_loc": 1})
        game.new_day()                       # N: về lại buổi sáng ban đầu
        self.assertEqual(game.mode, "gather")
        self.assertEqual(json.loads(game.state_json())["hold"], ["ca_loc", "bong_sung", "bong_sung"])

    def test_quan_mode_cannot_continue(self):
        game = LiveGame("quan", self.tuning, {}, 1)
        self.assertFalse(game.next_phase())

    def test_next_endpoint_and_assets(self):
        game = LiveGame("gather", self.tuning, {"hold": ["ca_linh"]}, 1)
        server = LiveServer(game, port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            with game._lock:
                game.session.sim.time_left_ticks = 1   # để luồng nền tự kết thúc buổi sáng
            self.assertIn(_post(base + "/next"), (200, 409))
            for _ in range(100):
                if game.mode == "quan" or game.can_continue():
                    break
                time.sleep(0.02)
            if game.mode == "gather":
                self.assertEqual(_post(base + "/next"), 200)
            snap = json.loads(urllib.request.urlopen(base + "/state", timeout=5).read())
            self.assertEqual(snap["mode"], "quan")
            self.assertEqual(snap["stock"], {"ca_linh": 1})
            url = base + "/assets/" + urllib.request.quote("Nền sông và nhân vật/PNG/environment/background.png")
            with urllib.request.urlopen(url, timeout=5) as r:
                self.assertTrue(r.read().startswith(b"\x89PNG\r\n\x1a\n"))
        finally:
            server.stop()

    def test_resolve_asset_blocks_escape_and_non_media(self):
        self.assertIsNotNone(resolve_asset("diver.png"))
        self.assertIsNotNone(resolve_asset("SpearFishing Assets Pack/Sprites/Fish3 - 32x16/Grey.png"))
        for bad in ("../game.contract.json", "..%2F..%2Fgame.contract.json", "../chonoi/live.py",
                    "Nền sông và nhân vật/code/lib/game/main.js", "/etc/passwd", "khong-co.png"):
            self.assertIsNone(resolve_asset(bad), bad)


if __name__ == "__main__":
    unittest.main()
