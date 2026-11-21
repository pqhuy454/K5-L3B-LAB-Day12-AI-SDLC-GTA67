"""Bộ kiểm thử chuyên sâu cho Lát 2: hái nút, bắt cá, cập bến, xuất/đọc file kho.

Chạy độc lập:
    PYTHONPATH=tests:. python -m unittest tests.test_gather_slice2 -v
"""

import json
import os
import subprocess
import sys
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session

from helpers import ROOT, Workdir, events, frames, read_jsonl, snapshots, write_json


def run_py_headless(*args: str, cwd: str = ROOT) -> tuple[int, str]:
    """Chạy `chonoi.headless` bằng chính interpreter đang chạy test (tương thích Windows/Linux/macOS)."""
    proc = subprocess.run(
        [sys.executable, "-m", "chonoi.headless", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stderr


class GatherSlice2HarvestTests(unittest.TestCase):
    def test_harvest_at_surface_collects_and_regrows(self) -> None:
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [12, 0]},
                        "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0]}],
                        "random_fish": False,
                    }
                },
            )
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True},
                    {"tick": 1, "interact": False},
                    {"tick": 10, "interact": True},
                    {"tick": 11, "interact": False},
                    {"tick": 1200, "interact": True},
                ),
            )
            out = w.path("g.jsonl")
            code, err = run_py_headless(
                "--mode", "gather", "--seed", "1", "--ticks", "1205",
                "--scenario", sc, "--inputs", inp, "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)

            gather_evs = events(rows, "gather")
            self.assertEqual(len(gather_evs), 2)
            self.assertEqual(gather_evs[0]["tick"], 1)
            self.assertEqual(
                gather_evs[0]["data"],
                {"node_id": "N1", "kind": "bong_dien_dien", "count": 1},
            )
            self.assertEqual(gather_evs[1]["tick"], 1201)

            regrown_evs = events(rows, "node_regrown")
            self.assertEqual(len(regrown_evs), 1)
            self.assertEqual(regrown_evs[0]["tick"], 1201)
            self.assertEqual(regrown_evs[0]["data"], {"node_id": "N1"})

            snaps = {s["tick"]: s for s in snapshots(rows)}
            self.assertEqual(snaps[1]["hold"], ["bong_dien_dien"])
            self.assertFalse(snaps[1]["nodes"][0]["ready"])
            self.assertEqual(snaps[1]["nodes"][0]["regrow_ticks"], 1200)
            self.assertEqual(snaps[11]["hold"], ["bong_dien_dien"])
            self.assertEqual(snaps[1201]["hold"], ["bong_dien_dien", "bong_dien_dien"])

    def test_harvest_requires_surface_and_radius_boundaries(self) -> None:
        tuning = load_contract()["tuning"]

        # Dưới nước (d = 0.6 > surface_depth = 0.5), cách nút 0.6 <= 2.0 -> không hái được
        sess_deep = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [12, 0.6]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                "random_fish": False,
            },
            seed=1,
        )
        pl_deep = InputPlayer([{"tick": 0, "interact": True}])
        evs_deep = sess_deep.step(pl_deep.advance(0))
        self.assertEqual(evs_deep, [])
        self.assertEqual(sess_deep.sim.hold, [])

        # Mặt nước nhưng ngoài bán kính (dist = 2.1 > 2.0) -> không hái được
        sess_far = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [14.1, 0]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                "random_fish": False,
            },
            seed=1,
        )
        pl_far = InputPlayer([{"tick": 0, "interact": True}])
        evs_far = sess_far.step(pl_far.advance(0))
        self.assertEqual(evs_far, [])
        self.assertEqual(sess_far.sim.hold, [])

        # Đúng biên mặt nước (d = 0.5) và khoảng cách <= 2.0 -> hái được
        sess_edge = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [13.5, 0.5]},
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                "random_fish": False,
            },
            seed=1,
        )
        pl_edge = InputPlayer([{"tick": 0, "interact": True}])
        evs_edge = sess_edge.step(pl_edge.advance(0))
        self.assertEqual([e["name"] for e in evs_edge], ["gather"])
        self.assertEqual(sess_edge.sim.hold, ["bong_sung"])

    def test_harvest_nearest_and_numeric_id_tiebreak(self) -> None:
        tuning = load_contract()["tuning"]

        # Hai nút cách đều nhau 1.0 m: N2 phải thắng N10 (theo id_key số học)
        sess_tie = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [20, 0]},
                "nodes": [
                    {"id": "N10", "kind": "bong_sung", "pos": [19, 0]},
                    {"id": "N2", "kind": "bong_dien_dien", "pos": [21, 0]},
                ],
                "random_fish": False,
            },
            seed=1,
        )
        evs_tie = sess_tie.step(InputPlayer([{"tick": 0, "interact": True}]).advance(0))
        self.assertEqual(len(evs_tie), 1)
        self.assertEqual(evs_tie[0]["data"]["node_id"], "N2")

        # Nút gần nhất chưa mọc (regrow_ticks > 0) -> chọn nút ready gần nhất trong tầm
        sess_skip = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [20, 0]},
                "nodes": [
                    {"id": "N1", "kind": "bong_dien_dien", "pos": [20, 0], "regrow_ticks": 50},
                    {"id": "N2", "kind": "bong_sung", "pos": [21.5, 0], "regrow_ticks": 0},
                ],
                "random_fish": False,
            },
            seed=1,
        )
        evs_skip = sess_skip.step(InputPlayer([{"tick": 0, "interact": True}]).advance(0))
        self.assertEqual(len(evs_skip), 1)
        self.assertEqual(evs_skip[0]["data"]["node_id"], "N2")

    def test_harvest_hold_full_keeps_node_ready_and_no_repeat_when_held(self) -> None:
        tuning = load_contract()["tuning"]
        cap = tuning["gather"]["hold_capacity"]
        sess = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [12, 0]},
                "hold": ["ca_loc"] * cap,
                "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                "random_fish": False,
            },
            seed=1,
        )
        player = InputPlayer([{"tick": 0, "interact": True}])
        evs0 = sess.step(player.advance(0))
        evs1 = sess.step(player.advance(1))  # giữ nút -> không lặp lại

        self.assertEqual(len(evs0), 1)
        self.assertEqual(evs0[0]["name"], "hold_full")
        self.assertEqual(
            evs0[0]["data"],
            {"source": "node", "id": "N1", "kind": "bong_sung", "needed": 1, "free": 0},
        )
        self.assertEqual(evs1, [])
        self.assertEqual(len(sess.sim.hold), cap)
        self.assertEqual(sess.sim.nodes[0]["regrow_ticks"], 0)


class GatherSlice2FishTests(unittest.TestCase):
    def test_catch_underwater_ca_linh_and_ca_loc_lifo_order(self) -> None:
        tuning = load_contract()["tuning"]
        sess = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [20, 10]},
                "hold": ["bong_sung"],
                "fish": [
                    {"id": "F1", "kind": "ca_linh", "pos": [20.5, 10]},
                    {"id": "F2", "kind": "ca_loc", "pos": [21.5, 10]},
                ],
            },
            seed=1,
        )
        player = InputPlayer(
            [
                {"tick": 0, "catch": True},
                {"tick": 1, "catch": False},
                {"tick": 30, "catch": True},
            ]
        )
        all_evs = []
        for tick in range(31):
            all_evs.extend(sess.step(player.advance(tick)))

        self.assertEqual(len(all_evs), 2)
        self.assertEqual(all_evs[0]["tick"], 1)
        self.assertEqual(all_evs[0]["name"], "fish_caught")
        self.assertEqual(
            all_evs[0]["data"],
            {"fish_id": "F1", "kind": "ca_linh", "count": 3},
        )
        self.assertEqual(all_evs[1]["tick"], 31)
        self.assertEqual(all_evs[1]["name"], "fish_caught")
        self.assertEqual(
            all_evs[1]["data"],
            {"fish_id": "F2", "kind": "ca_loc", "count": 1},
        )
        self.assertEqual(sess.sim.hold, ["bong_sung", "ca_linh", "ca_linh", "ca_linh", "ca_loc"])
        self.assertEqual(sess.sim.fish, [])
        self.assertEqual(sess.sim.catch_cd_ticks, 30)

    def test_catch_blocked_on_tick_29_and_allowed_on_tick_30(self) -> None:
        tuning = load_contract()["tuning"]
        sess = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [20, 10]},
                "fish": [
                    {"id": "F1", "kind": "ca_loc", "pos": [20, 10]},
                    {"id": "F2", "kind": "ca_loc", "pos": [20.5, 10]},
                ],
            },
            seed=1,
        )
        player = InputPlayer(
            [
                {"tick": 0, "catch": True},
                {"tick": 1, "catch": False},
                {"tick": 29, "catch": True},  # cooldown còn 1 -> phải bị chặn
            ]
        )
        evs = []
        for tick in range(30):
            evs.extend(sess.step(player.advance(tick)))

        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["data"]["fish_id"], "F1")
        self.assertEqual(len(sess.sim.fish), 1)
        self.assertEqual(sess.sim.catch_cd_ticks, 1)

    def test_catch_requires_underwater_and_miss_does_not_trigger_cooldown(self) -> None:
        tuning = load_contract()["tuning"]

        # Đang ở mặt nước (d = 0.5), cá ở [20, 1.0] cách 0.5 m -> không được bắt
        sess_surface = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [20, 0.5]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 1.0]}],
            },
            seed=1,
        )
        evs_surface = sess_surface.step(InputPlayer([{"tick": 0, "catch": True}]).advance(0))
        self.assertEqual(evs_surface, [])
        self.assertEqual(len(sess_surface.sim.fish), 1)
        self.assertEqual(sess_surface.sim.catch_cd_ticks, 0)

        # Dưới nước nhưng cá ngoài bán kính (2.1 m) -> trượt, không kích hoạt cooldown
        sess_miss = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [20, 10]},
                "fish": [{"id": "F1", "kind": "ca_loc", "pos": [22.1, 10]}],
            },
            seed=1,
        )
        evs_miss = sess_miss.step(InputPlayer([{"tick": 0, "catch": True}]).advance(0))
        self.assertEqual(evs_miss, [])
        self.assertEqual(sess_miss.sim.catch_cd_ticks, 0)

    def test_catch_numeric_id_tiebreak(self) -> None:
        tuning = load_contract()["tuning"]
        sess = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [30, 10]},
                "fish": [
                    {"id": "F10", "kind": "ca_loc", "pos": [29, 10]},
                    {"id": "F2", "kind": "ca_loc", "pos": [31, 10]},
                ],
            },
            seed=1,
        )
        evs = sess.step(InputPlayer([{"tick": 0, "catch": True}]).advance(0))
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["data"]["fish_id"], "F2")

    def test_catch_forbids_partial_and_no_fallback_to_farther_school(self) -> None:
        tuning = load_contract()["tuning"]
        # Giỏ còn 2 chỗ trống; F1 gần hơn (0.5 m) là ca_linh (yield=3), F2 xa hơn (1.0 m) là ca_loc (yield=1)
        sess = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [30, 10]},
                "hold": ["bong_sung"] * 10,
                "fish": [
                    {"id": "F1", "kind": "ca_linh", "pos": [30.5, 10]},
                    {"id": "F2", "kind": "ca_loc", "pos": [31.0, 10]},
                ],
            },
            seed=1,
        )
        evs = sess.step(InputPlayer([{"tick": 0, "catch": True}]).advance(0))
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["name"], "hold_full")
        self.assertEqual(
            evs[0]["data"],
            {"source": "fish", "id": "F1", "kind": "ca_linh", "needed": 3, "free": 2},
        )
        self.assertEqual(len(sess.sim.hold), 10)
        self.assertEqual([f["id"] for f in sess.sim.fish], ["F1", "F2"])
        self.assertEqual(sess.sim.catch_cd_ticks, 0)


class GatherSlice2DockAndInventoryTests(unittest.TestCase):
    def test_dock_takes_priority_over_harvest_and_catch(self) -> None:
        tuning = load_contract()["tuning"]
        sess = Session(
            "gather",
            tuning,
            {
                "player": {"pos": [3, 0]},  # trong dock_radius=3 từ [2,0] VÀ đứng ngay tại nút N1
                "hold": ["ca_loc"],
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [3, 0]}],
                "random_fish": False,
            },
            seed=1,
        )
        evs = sess.step(InputPlayer([{"tick": 0, "interact": True, "catch": True}]).advance(0))
        self.assertEqual([e["name"] for e in evs], ["gather_end"])
        self.assertEqual(evs[0]["data"]["reason"], "docked")
        self.assertEqual(evs[0]["data"]["inventory"], {"items": {"ca_loc": 1}})
        self.assertTrue(sess.done)

    def test_mandatory_spec_two_process_smoke_transfer(self) -> None:
        with Workdir() as w:
            sc = write_json(w.path("dock.json"), {"gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"]}})
            inp = write_json(w.path("dock-inputs.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("catch.json")
            g_out = w.path("gather.jsonl")
            q_out = w.path("quan.jsonl")

            code, err = run_py_headless(
                "--mode", "gather", "--seed", "42", "--scenario", sc, "--inputs", inp,
                "--ticks", "1", "--out", g_out, "--inventory-out", inv,
            )
            self.assertEqual(code, 0, err)
            with open(inv, "rb") as f:
                raw_inv = f.read()
            self.assertEqual(raw_inv, b'{"items":{"bong_sung":2,"ca_loc":1}}\n')

            code, err = run_py_headless(
                "--mode", "quan", "--seed", "42", "--inventory", inv, "--ticks", "0", "--out", q_out,
            )
            self.assertEqual(code, 0, err)
            q_snap = snapshots(read_jsonl(q_out))[0]
            self.assertEqual(q_snap["stock"], {"bong_sung": 2, "ca_loc": 1})

    def test_end_to_end_harvest_catch_dock_transfer_and_determinism(self) -> None:
        with Workdir() as w:
            sc = write_json(
                w.path("sc.json"),
                {
                    "gather": {
                        "player": {"pos": [6, 0]},
                        "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [6, 0]}],
                        "fish": [{"id": "F1", "kind": "ca_linh", "pos": [6, 2]}],
                    }
                },
            )
            # Tick 0: hái N1 tại [6,0], rồi bơi xuống [6,2] (~33 tick), bắt F1 tại tick 45,
            # bơi về bến [2,0] (~75 tick) và cập bến tại tick 140
            inp = write_json(
                w.path("in.json"),
                frames(
                    {"tick": 0, "interact": True, "move": [0, 1]},
                    {"tick": 1, "interact": False},
                    {"tick": 35, "move": [0, 0]},
                    {"tick": 45, "catch": True, "move": [-1, -0.5]},
                    {"tick": 46, "catch": False},
                    {"tick": 135, "move": [0, 0]},
                    {"tick": 140, "interact": True},
                ),
            )
            out1, inv1 = w.path("g1.jsonl"), w.path("inv1.json")
            out2, inv2 = w.path("g2.jsonl"), w.path("inv2.json")

            for out_p, inv_p in ((out1, inv1), (out2, inv2)):
                code, err = run_py_headless(
                    "--mode", "gather", "--seed", "7", "--scenario", sc, "--inputs", inp,
                    "--ticks", "200", "--out", out_p, "--inventory-out", inv_p,
                )
                self.assertEqual(code, 0, err)

            with open(out1, "rb") as a, open(out2, "rb") as b:
                self.assertEqual(a.read(), b.read())
            with open(inv1, "rb") as a, open(inv2, "rb") as b:
                raw1, raw2 = a.read(), b.read()
                self.assertEqual(raw1, raw2)
                self.assertEqual(raw1, b'{"items":{"bong_dien_dien":1,"ca_linh":3}}\n')

            rows = read_jsonl(out1)
            self.assertEqual(len(events(rows, "gather")), 1)
            self.assertEqual(len(events(rows, "fish_caught")), 1)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")

            q_out = w.path("q.jsonl")
            code, err = run_py_headless(
                "--mode", "quan", "--seed", "7", "--inventory", inv1, "--ticks", "0", "--out", q_out,
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(
                snapshots(read_jsonl(q_out))[0]["stock"],
                {"bong_dien_dien": 1, "ca_linh": 3},
            )

    def test_tick_limit_does_not_write_inventory_and_time_writes_harvested_items(self) -> None:
        with Workdir() as w:
            sc_limit = write_json(
                w.path("sc_limit.json"),
                {
                    "gather": {
                        "player": {"pos": [12, 0]},
                        "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                        "random_fish": False,
                    }
                },
            )
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv_limit = w.path("no_inv.json")
            code, err = run_py_headless(
                "--mode", "gather", "--seed", "1", "--scenario", sc_limit, "--inputs", inp,
                "--ticks", "5", "--out", w.path("l.jsonl"), "--inventory-out", inv_limit,
            )
            self.assertEqual(code, 0, err)
            self.assertFalse(os.path.exists(inv_limit))

            sc_time = write_json(
                w.path("sc_time.json"),
                {
                    "gather": {
                        "player": {"pos": [12, 0]},
                        "time_left_ticks": 3,
                        "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [12, 0]}],
                        "random_fish": False,
                    }
                },
            )
            inv_time = w.path("time_inv.json")
            code, err = run_py_headless(
                "--mode", "gather", "--seed", "1", "--scenario", sc_time, "--inputs", inp,
                "--ticks", "10", "--out", w.path("t.jsonl"), "--inventory-out", inv_time,
            )
            self.assertEqual(code, 0, err)
            with open(inv_time, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {"bong_sung": 1}})


if __name__ == "__main__":
    unittest.main()
