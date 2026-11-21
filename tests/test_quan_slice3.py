"""Unit test cho Lát 3 (Khách hàng & Đơn món trong QuanSim)."""

import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


class TestQuanSlice3(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def _make_sim(self, stock=None, scenario=None, seed=42):
        sc = scenario or {}
        if stock is not None:
            sc["stock"] = stock
        return QuanSim(self.tuning, sc, Streams(seed), IdAllocator())

    def test_customer_arrival_at_first_tick(self):
        # Có đủ nguyên liệu nấu cá lóc nướng trui
        sim = self._make_sim(stock={"ca_loc": 2})
        ip = InputPlayer([])

        # Chạy 119 tick, chưa có khách
        for t in range(119):
            events = sim.step(ip.advance(t))
            self.assertEqual(len(sim.customers), 0)

        # Tick 120: Khách C1 xuất hiện
        events = sim.step(ip.advance(119))
        self.assertEqual(len(sim.customers), 1)
        c = sim.customers[0]
        self.assertEqual(c["id"], "C1")
        self.assertEqual(c["table_id"], "T1")
        self.assertEqual(c["dish_id"], "ca_loc_nuong_trui")
        self.assertEqual(c["state"], "waiting")
        self.assertEqual(c["patience_ticks_left"], 3600)
        self.assertEqual(c["reserved"], {"ca_loc": 1})

        # Kho thực tế vẫn là 2, nhưng kho khả dụng chỉ còn 1
        self.assertEqual(sim.stock["ca_loc"], 2)
        self.assertEqual(sim.available_stock()["ca_loc"], 1)

        # Kiểm tra event
        arrived = [e for e in events if e[0] == "customer_arrived"]
        self.assertEqual(len(arrived), 1)
        self.assertEqual(arrived[0][1]["customer_id"], "C1")
        self.assertEqual(arrived[0][1]["dish_id"], "ca_loc_nuong_trui")

    def test_no_dish_when_stock_empty(self):
        # Kho rỗng
        sim = self._make_sim(stock={})
        ip = InputPlayer([])

        for t in range(119):
            sim.step(ip.advance(t))

        # Tick 120: Không đủ nguyên liệu nấu món nào -> phát no_dish
        events = sim.step(ip.advance(119))
        self.assertEqual(len(sim.customers), 0)
        no_dish = [e for e in events if e[0] == "no_dish"]
        self.assertEqual(len(no_dish), 1)
        self.assertEqual(no_dish[0][1]["table_id"], "T1")

    def test_no_double_seat_when_table_occupied(self):
        # Có nhiều nguyên liệu
        sim = self._make_sim(stock={"ca_loc": 10})
        ip = InputPlayer([])

        # Tick 120: Khách C1 ngồi bàn T1
        for t in range(120):
            sim.step(ip.advance(t))
        self.assertEqual(len(sim.customers), 1)

        # Chạy tiếp 900 tick tới tick 1020 (chu kỳ khách tiếp theo)
        for t in range(120, 1020):
            events = sim.step(ip.advance(t))

        # Bàn T1 vẫn đang có C1 ngồi, không tạo thêm khách
        self.assertEqual(len(sim.customers), 1)
        self.assertEqual(sim.customers[0]["id"], "C1")

    def test_patience_countdown_and_customer_left(self):
        sim = self._make_sim(stock={"ca_loc": 2})
        ip = InputPlayer([])

        for t in range(120):
            sim.step(ip.advance(t))

        c = sim.customers[0]
        initial_patience = c["patience_ticks_left"]
        self.assertEqual(initial_patience, 3600)
        initial_rep = sim.reputation

        # Chạy 3599 tick tiếp theo: kiên nhẫn giảm dần nhưng khách chưa đi
        for i in range(3599):
            sim.step(ip.advance(120 + i))
            self.assertEqual(len(sim.customers), 1)
            self.assertEqual(sim.customers[0]["patience_ticks_left"], initial_patience - 1 - i)

        # Tick cuối cùng (3600 tick trôi qua kể từ khi C1 vào ở tick 120 -> tổng 3720 tick):
        # C1 hết kiên nhẫn bỏ về. Vì tick 3720 cũng là mốc chu kỳ đón khách (120 + 4*900 = 3720),
        # bàn T1 vừa trống và kho còn ca_loc nên khách mới C2 được đón vào bàn.
        events = sim.step(ip.advance(120 + 3599))
        self.assertAlmostEqual(sim.reputation, initial_rep - 0.5)

        left = [e for e in events if e[0] == "customer_left"]
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0][1]["customer_id"], "C1")
        self.assertEqual(left[0][1]["reason"], "patience")

        arrived = [e for e in events if e[0] == "customer_arrived"]
        self.assertEqual(len(arrived), 1)
        self.assertEqual(arrived[0][1]["customer_id"], "C2")
        self.assertEqual(sim.customers[0]["id"], "C2")

    def test_closing_waiting_customer_leaves_no_penalty(self):
        # Scenario gần hết giờ, có 1 khách đang chờ
        scenario = {
            "time_left_ticks": 5,
            "stock": {"ca_loc": 1},
            "customers": [{
                "id": "C9",
                "table_id": "T1",
                "dish_id": "ca_loc_nuong_trui",
                "state": "waiting",
                "patience_ticks_left": 1000
            }]
        }
        sim = self._make_sim(scenario=scenario)
        initial_rep = sim.reputation
        ip = InputPlayer([])

        for t in range(4):
            sim.step(ip.advance(t))
            self.assertFalse(sim.done)

        # Tick thứ 5: hết ca (time_left_ticks = 0)
        events = sim.step(ip.advance(4))
        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "time")
        # Không bị trừ uy tín
        self.assertEqual(sim.reputation, initial_rep)

        left = [e for e in events if e[0] == "customer_left"]
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0][1]["customer_id"], "C9")
        self.assertEqual(left[0][1]["reason"], "closing")


if __name__ == "__main__":
    unittest.main()
