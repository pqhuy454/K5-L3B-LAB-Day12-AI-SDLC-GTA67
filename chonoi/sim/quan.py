"""Buổi tối — Mở Quán. Hợp nhất Lát 3 (Khách & Đơn) và Lát 4 (Bếp, Phục vụ, Tiền, Uy tín).

Lát 3 (Khách & Đơn — Đặng Đức Minh):
  - Khách đến theo lịch (first_customer_tick, customer_interval_s).
  - Chọn món nấu được từ kho khả dụng (physical_stock - reserved), chọn đều có hạt giống (customer_order).
  - Giữ chỗ nguyên liệu (reserved).
  - Đếm lùi kiên nhẫn (patience_ticks_left), bỏ đi khi hết giờ (customer_left), trừ uy tín.
  - Sự kiện no_dish khi bàn trống nhưng không đủ nguyên liệu nấu món nào.
  - Đóng ca: khách chờ về không bị phạt uy tín.
Lát 4 (Bếp & Phục vụ — Phạm Quốc Huy):
  - `quan_kitchen.py` & `ledger.py`: tick bếp/ăn, interact bếp/bàn (cook_started, dish_ready,
    dish_picked, served), ăn xong trả tiền (paid), boa, uy tín, bỏ món khi khách rời, đóng ca.
"""

from ..ids import sort_by_id
from . import ledger, pick, quan_kitchen as kitchen, quan_orders as orders
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        total_dur = int(round(t["duration_s"] * TICK))
        self.sim_tick = scenario.get("sim_tick", total_dur - self.time_left_ticks)
        self.step_no = 0
        self.random_customers = scenario.get("random_customers", True)
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            customer_id=s.get("customer_id"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))

        # Khách dựng sẵn từ scenario và suy ra giữ chỗ (reserved)
        self.customers = []
        for c in scenario.get("customers", []):
            cust = dict(c)
            dish_id = cust.get("dish_id") or cust.get("dish")
            if dish_id:
                cust["dish_id"] = dish_id
            if "state" not in cust:
                cust["state"] = "waiting"
            if "patience_ticks_left" not in cust:
                cust["patience_ticks_left"] = cust.get("patience_ticks", int(round(t["patience_s"] * TICK)))
            if "reserved" not in cust:
                if cust["state"] == "waiting" and dish_id and dish_id in self.menu:
                    cust["reserved"] = dict(self.menu[dish_id]["recipe"])
                else:
                    cust["reserved"] = {}
            else:
                cust["reserved"] = dict(cust["reserved"])
            self.customers.append(cust)
            ids.reserve(cust["id"])

        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None
        orders.on_load(self)
        kitchen.on_load(self)

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def available_stock(self) -> dict:
        """Kho khả dụng = kho thực tế - nguyên liệu đang được khách giữ chỗ."""
        avail = dict(self.stock)
        for c in self.customers:
            for item, qty in c.get("reserved", {}).items():
                avail[item] = avail.get(item, 0) - qty
        return avail

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos, "vel": self.vel},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "customer_id", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": [{k: v for k, v in c.items() if not k.startswith("_")}
                          for c in sort_by_id(self.customers)],
        }

    def _targets(self):
        return [(0, s) for s in self.stoves] + [(1, tb) for tb in self.tables]

    def step(self, inp):
        events = []
        self.step_no += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.sim_tick += 1

        # 1. Giảm kiên nhẫn khách chờ (Lát 3) + cập nhật bếp & khách đang ăn (Lát 4)
        for c in self.customers:
            if c.get("state") == "waiting":
                c["patience_ticks_left"] -= 1
        kitchen.tick_stoves(self, events)
        kitchen.tick_eating(self, events)

        # 2. Di chuyển người chơi
        self._move(inp)

        # 3. Tương tác tối đa MỘT đối tượng (Lát 4): chọn theo (khoảng cách, bếp trước bàn, id), không fallback
        if inp.pressed("interact"):
            target = pick.nearest(self.pos, self._targets(), self.t["interact_radius"])
            if target is not None:
                kitchen.interact(self, target, events)

        # 4. Xử lý khách hết kiên nhẫn bỏ về (phục vụ đúng tick kiên nhẫn chạm 0 ở bước 3 vẫn hợp lệ)
        remaining_customers = []
        for c in self.customers:
            if c.get("state") == "waiting" and c["patience_ticks_left"] <= 0:
                ledger.add_reputation(self, self.t["left_reputation_delta"])
                kitchen.discard_dish_for(self, c["id"])
                events.append(("customer_left", {
                    "customer_id": c["id"],
                    "reason": "patience",
                    "table_id": c["table_id"],
                }))
            else:
                remaining_customers.append(c)
        self.customers = remaining_customers

        # 5. Khách mới theo lịch (first_customer_tick, customer_interval_s)
        first_tick = self.t["first_customer_tick"]
        interval = int(round(self.t["customer_interval_s"] * TICK))
        if self.random_customers and self.sim_tick >= first_tick and (self.sim_tick - first_tick) % interval == 0:
            occupied = {c["table_id"] for c in self.customers}
            free_tables = [tb for tb in self.tables if tb["id"] not in occupied]
            if free_tables:
                target_table = free_tables[0]
                avail = self.available_stock()
                possible_dishes = [
                    d for d in sorted(self.menu.keys())
                    if all(avail.get(item, 0) >= qty for item, qty in self.menu[d]["recipe"].items())
                ]
                if not possible_dishes:
                    events.append(("no_dish", {"table_id": target_table["id"]}))
                else:
                    chosen = self.rng.get("customer_order").choice(possible_dishes)
                    cid = self.ids.new("C")
                    recipe = dict(self.menu[chosen]["recipe"])
                    new_cust = {
                        "id": cid,
                        "table_id": target_table["id"],
                        "dish_id": chosen,
                        "state": "waiting",
                        "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
                        "reserved": recipe,
                        "_cooking": False,
                    }
                    self.customers.append(new_cust)
                    events.append(("customer_arrived", {
                        "customer_id": cid,
                        "table_id": target_table["id"],
                        "dish_id": chosen,
                    }))

        # 6. Hết đồ ăn (chỉ bật ở live qua end_when_out_of_stock) hoặc Hết giờ / Đóng ca
        if (self.t.get("end_when_out_of_stock", False) and not self.customers
                and self.hand is None and all(s["state"] == "idle" for s in self.stoves)):
            avail = self.available_stock()
            can_cook_any = any(
                all(avail.get(item, 0) >= qty for item, qty in d["recipe"].items())
                for d in self.menu.values()
            )
            if not can_cook_any:
                self.done = True
                self.reason = "out_of_stock"
                events.append(("quan_end", {
                    "reason": "out_of_stock",
                    "money": self.money,
                    "earned": self.earned,
                    "shift_earned": self.shift_earned,
                    "reputation": self.reputation,
                }))
                return events

        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            kitchen.close_shift(self, events)
            for c in self.customers:
                if c.get("state") == "waiting":
                    events.append(("customer_left", {
                        "customer_id": c["id"],
                        "reason": "closing",
                        "table_id": c["table_id"],
                    }))
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
            }))

        return events

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
