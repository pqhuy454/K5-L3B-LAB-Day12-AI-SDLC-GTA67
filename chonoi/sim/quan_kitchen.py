"""Lát 4 — Bếp, bưng món, phục vụ, ăn, trả tiền, tiền boa, uy tín và đóng ca.

Chủ: Phạm Quốc Huy (pqhuy454).
Chỉ phụ thuộc một chiều vào quan_orders và ledger (không import quan.py).
Mọi số liệu đọc từ sim.t và sim.menu (không hard-code).
"""

import math

from ..errors import BadInput
from ..ids import sort_by_id
from . import ledger, quan_orders as orders

TICK = 60.0
VALID_STOVE_STATES = ("idle", "cooking", "ready")
VALID_CUSTOMER_STATES = ("waiting", "eating")


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _cust_dish(customer: dict):
    return customer.get("dish_id") or customer.get("dish")


def _cust_patience(customer: dict) -> int:
    if "patience_ticks_left" in customer:
        return customer["patience_ticks_left"]
    return customer.get("patience_ticks", 0)


def _clear_stove(stove: dict) -> None:
    stove["state"] = "idle"
    stove["dish"] = None
    stove["customer_id"] = None
    stove["cook_ticks_left"] = 0
    stove["ready_ticks"] = 0


def validate_scenario(block: dict, tuning: dict) -> None:
    menu = tuning["menu"]
    hand = block.get("hand")
    if hand is not None:
        if not isinstance(hand, dict) or hand.get("dish") not in menu:
            raise BadInput("quan.hand phải là null hoặc object có dish hợp lệ trong menu")
        cid = hand.get("customer_id")
        if cid is not None and (not isinstance(cid, str) or not cid):
            raise BadInput("quan.hand.customer_id phải là chuỗi khác rỗng hoặc null")

    for s in block.get("stoves", []):
        st = s.get("state", "idle")
        if st not in VALID_STOVE_STATES:
            raise BadInput(f"stoves.{s['id']}: state không hợp lệ ({st!r})")
        dish = s.get("dish")
        ctl = s.get("cook_ticks_left", 0)
        rt = s.get("ready_ticks", 0)
        if not _is_int(ctl) or ctl < 0:
            raise BadInput(f"stoves.{s['id']}: cook_ticks_left phải là số nguyên không âm")
        if not _is_int(rt) or rt < 0:
            raise BadInput(f"stoves.{s['id']}: ready_ticks phải là số nguyên không âm")
        if st == "idle":
            if dish is not None or ctl != 0:
                raise BadInput(f"stoves.{s['id']}: bếp idle không được có dish hoặc cook_ticks_left > 0")
        elif st == "cooking":
            if dish not in menu or ctl <= 0:
                raise BadInput(f"stoves.{s['id']}: bếp cooking cần dish hợp lệ và cook_ticks_left >= 1")
        elif st == "ready":
            if dish not in menu or ctl != 0:
                raise BadInput(f"stoves.{s['id']}: bếp ready cần dish hợp lệ và cook_ticks_left == 0")

    for c in block.get("customers", []):
        st = c.get("state", "waiting")
        if st not in VALID_CUSTOMER_STATES:
            raise BadInput(f"customers.{c['id']}: state không hợp lệ ({st!r})")
        if st == "eating":
            if _cust_dish(c) not in menu:
                raise BadInput(f"customers.{c['id']}: khách eating cần dish hợp lệ trong menu")
            et = c.get("eat_ticks")
            if not _is_int(et) or et <= 0:
                raise BadInput(f"customers.{c['id']}: khách eating cần eat_ticks >= 1")
            if "tip" in c and (not _is_int(c["tip"]) or c["tip"] < 0):
                raise BadInput(f"customers.{c['id']}: tip phải là số nguyên không âm")


def on_load(sim) -> None:
    for s in sim.stoves:
        s.setdefault("customer_id", None)
        s.setdefault("cook_ticks_left", 0)
        s.setdefault("ready_ticks", 0)
    for c in sim.customers:
        if c.get("state") == "eating":
            c.setdefault("tip", 0)


def tick_stoves(sim, events: list) -> None:
    for s in sort_by_id(sim.stoves):
        if s["state"] == "cooking":
            s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            if s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                events.append(("dish_ready", {"stove_id": s["id"], "dish": s["dish"]}))
        elif s["state"] == "ready":
            # Phase 1: burn_s là null nên món không cháy, chỉ đếm thời gian chín.
            s["ready_ticks"] += 1


def _pay_customer(sim, customer: dict, events: list) -> None:
    price = sim.menu[_cust_dish(customer)]["price"]
    tip = int(customer.get("tip", 0))
    amount = price + tip
    ledger.add_money(sim, amount)
    if tip > 0:
        ledger.add_reputation(sim, sim.t["tip_reputation"])
    events.append(("paid", {"customer_id": customer["id"], "amount": amount, "tip": tip}))
    orders.remove(sim, customer)


def tick_eating(sim, events: list) -> None:
    eating = sort_by_id([c for c in sim.customers if c.get("state") == "eating"])
    manual = bool(sim.t.get("manual_collect", False))
    for c in eating:
        c["eat_ticks"] = max(0, c["eat_ticks"] - 1)
        if c["eat_ticks"] == 0:
            if manual:
                c["state"] = "ready_to_pay"
            else:
                _pay_customer(sim, c, events)


def interact(sim, target: tuple, events: list) -> None:
    rank, obj = target
    if rank == 0:
        _interact_stove(sim, obj, events)
    elif rank == 1:
        _interact_table(sim, obj, events)


def _interact_stove(sim, stove: dict, events: list) -> None:
    if sim.hand is not None:
        return
    if stove["state"] == "ready":
        dish = stove["dish"]
        sim.hand = {"dish": dish, "customer_id": stove.get("customer_id")}
        _clear_stove(stove)
        events.append(("dish_picked", {"stove_id": stove["id"], "dish": dish}))
    elif stove["state"] == "idle":
        customer = orders.pending_order(sim)
        if customer is None:
            return
        dish = _cust_dish(customer)
        orders.consume_reserved(sim, customer)
        stove["state"] = "cooking"
        stove["dish"] = dish
        stove["customer_id"] = customer["id"]
        stove["cook_ticks_left"] = int(round(sim.menu[dish]["cook_s"] * TICK))
        stove["ready_ticks"] = 0
        events.append(("cook_started", {"stove_id": stove["id"], "dish": dish, "customer_id": customer["id"]}))


def _interact_table(sim, table: dict, events: list) -> None:
    customer = orders.customer_at_table(sim, table["id"])
    if customer is None:
        return
    if customer.get("state") == "ready_to_pay":
        _pay_customer(sim, customer, events)
        return
    if sim.hand is None or customer.get("state") != "waiting":
        return
    dish = sim.hand["dish"]
    hand_cid = sim.hand.get("customer_id")
    if _cust_dish(customer) != dish:
        return
    if hand_cid is not None and hand_cid != customer["id"]:
        return

    sim.hand = None
    patience_max = int(round(sim.t["patience_s"] * TICK))
    patience_left = _cust_patience(customer)
    price = sim.menu[dish]["price"]
    if patience_left >= patience_max * sim.t["tip_min_patience_ratio"]:
        tip = math.floor(price * sim.t["tip_rate"])
    else:
        tip = 0

    customer["state"] = "eating"
    customer["eat_ticks"] = int(round(sim.t["eat_s"] * TICK))
    customer["tip"] = tip
    events.append(("served", {"customer_id": customer["id"], "dish": dish, "tip": tip}))


def discard_dish_for(sim, customer_id: str) -> None:
    for s in sim.stoves:
        if s.get("customer_id") == customer_id:
            _clear_stove(s)
    if sim.hand is not None and sim.hand.get("customer_id") == customer_id:
        sim.hand = None


def close_shift(sim, events: list) -> None:
    payable = sort_by_id([c for c in sim.customers if c.get("state") in ("eating", "ready_to_pay")])
    for c in payable:
        _pay_customer(sim, c, events)
