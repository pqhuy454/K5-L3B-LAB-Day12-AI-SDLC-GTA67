# Hợp đồng hook giữa bộ điều phối và các lát (contract nội bộ)

> Chủ hợp đồng: **Phạm Quốc Huy (Integrator)**. Đổi chữ ký hàm hoặc quyền ghi trường thì sửa file này **trước**, báo nhóm, rồi mới sửa code.
> Mọi hàm lát nhận `sim` (đối tượng `GatherSim`/`QuanSim`) và `events` (list để `append((name, data))`). Không hàm nào được import `gather.py`/`quan.py`.

## 1. Helper dùng chung (viết ĐẦY ĐỦ trong commit khung)

### `chonoi/sim/pick.py` — Chủ: Integrator

```python
def nearest(pos, candidates, radius):
    """candidates: iterable các cặp (rank, obj), obj có 'id' và 'pos'.
    Trả cặp (rank, obj) có khóa nhỏ nhất (khoảng cách, rank, id_key(id)) với khoảng cách <= radius, hoặc None.
    rank dùng để phá hòa: quán thì bếp = 0, bàn = 1; buổi sáng truyền rank = 0."""
```

Dùng bởi: Lát 2 (nút hái, đàn cá), bộ điều phối quán (bếp/bàn). Chỉ trả **một** đối tượng: không có fallback (FR-040).

### `chonoi/sim/hold.py` — Chủ: Trần Duy Thành (Lát 1)

```python
def free_slots(sim) -> int            # hold_capacity - len(sim.hold)
def push_all(sim, kinds: list) -> bool  # đủ chỗ cho CẢ list thì extend và trả True; không thì không đổi, trả False
def clear(sim) -> None                # giỏ rỗng (dùng khi ngất)
```

Chỉ `hold.py` được ghi `sim.hold`. Lát 2 thêm món **chỉ qua** `push_all`.

### `chonoi/sim/ledger.py` — Chủ: Phạm Quốc Huy (Lát 4)

```python
def add_money(sim, amount: int) -> None        # money, earned, shift_earned cùng tăng
def add_reputation(sim, delta: float) -> None  # cộng rồi kẹp [reputation_min, reputation_max], làm tròn 6 chữ số
```

Chỉ `ledger.py` được ghi `money/earned/shift_earned/reputation`. Làm tròn để `3 + 0.2×10` không thành `4.999999…` (floor ra 4 làm sai điểm).

## 2. Buổi sáng

### Thứ tự một bước — `GatherSim.step()` (Chủ: Integrator, viết trong commit khung)

```python
def step(self, inp):
    events = []
    self._tick_timers(events)                      # khung: time_left, invuln, catch_cd, nút mọc lại (node_regrown)
    was_surface = self._at_surface()
    self._move(inp)                                # khung: ramp + chặn mép
    survival.zone_change(self, was_surface, events)            # L1
    if survival.update_oxygen(self, events):                   # L1 — True nếu vừa ngất
        self._finish("fainted", events); return events
    if inp.pressed("interact"):
        if self._in_dock():
            self._finish("docked", events); return events
        harvest.try_gather(self, events)                       # L2
    if inp.pressed("catch"):
        harvest.try_catch(self, events)                        # L2
    if self.time_left_ticks <= 0:
        self._finish("time", events)
    return events
```

### `chonoi/sim/gather_survival.py` — Chủ: Trần Duy Thành (Lát 1)

| Hàm | Làm gì | FR |
|---|---|---|
| `zone_change(sim, was_surface, events)` | So vùng đầu/cuối bước → `dive` / `surface` | FR-011 |
| `update_oxygen(sim, events) -> bool` | Oxy theo d cuối bước, `oxygen_empty`, đếm ngạt, `choke`, Máu. Máu 0 → `hold.clear(sim)`, phát `faint`, trả `True` | FR-012..014 |

### `chonoi/sim/gather_harvest.py` — Chủ: Đoàn Anh Hùng (Lát 2)

| Hàm | Làm gì | FR |
|---|---|---|
| `try_gather(sim, events)` | Chỉ khi `sim._at_surface()`. `pick.nearest` trên nút `regrow_ticks == 0`, rồi `hold.push_all` → `gather` (đặt `regrow_ticks`) hoặc `hold_full` | FR-021 |
| `try_catch(sim, events)` | Chỉ khi dưới nước và `catch_cd_ticks == 0`. `pick.nearest` trên `sim.fish`, rồi `push_all([kind]*yield)` → `fish_caught` (xóa đàn, đặt hồi chiêu) hoặc `hold_full` | FR-023 |

### Ma trận quyền ghi — buổi sáng

| Trường trên `sim` | Được GHI bởi | Ghi chú |
|---|---|---|
| `pos`, `vel`, `heading`, `_tgt`, `_ramp_left` | bộ điều phối (`_move`) | |
| `time_left_ticks`, giảm `invuln_ticks`/`catch_cd_ticks`, đếm ngược `nodes[*].regrow_ticks` | bộ điều phối (`_tick_timers`) | |
| `oxygen_ticks`, `zero_oxy_ticks`, `hp` | L1 | |
| `hold` | `hold.py` (L1) | L2 qua `push_all`, L1 qua `clear` |
| đặt `catch_cd_ticks`, đặt `nodes[*].regrow_ticks`, xóa phần tử `fish` | L2 | |
| `done`, `reason` | bộ điều phối (`_finish`) | |

## 3. Buổi tối

### Thứ tự một bước — `QuanSim.step()` (Chủ: Integrator, viết trong commit khung)

> ⚠️ Thứ tự này là **đề xuất** khớp với các ràng buộc đã biết: "phục vụ đúng bước kiên nhẫn về 0 vẫn hợp lệ" nên bỏ đi xét **sau** interact, và "tip tính sau khi giảm kiên nhẫn của bước đó" nên giảm kiên nhẫn xét **trước** interact. PO đối chiếu Test Contract §F. Nếu khác, **chỉ Integrator đổi thứ tự ở đây**, còn các lát không phải sửa gì.

```python
def step(self, inp):
    events = []
    self.step_no += 1
    self.time_left_ticks = max(0, self.time_left_ticks - 1)
    orders.tick_patience(self, events)                         # L3
    kitchen.tick_stoves(self, events)                          # L4 → dish_ready
    kitchen.tick_eating(self, events)                          # L4 → paid
    self._move(inp)
    if inp.pressed("interact"):
        target = pick.nearest(self.pos, self._targets(), self.t["interact_radius"])
        if target is not None:
            kitchen.interact(self, target, events)             # L4
    for cid in orders.process_departures(self, events):        # L3 → customer_left
        kitchen.discard_dish_for(self, cid)                    # L4
    orders.spawn_if_due(self, events)                          # L3 → khách mới / no_dish
    if self.time_left_ticks <= 0:
        kitchen.close_shift(self, events)                      # L4: khách đang ăn trả ngay
        orders.close_shift(self, events)                       # L3: khách đang chờ rời, không phạt
        self._finish(events)                                   # khung: quan_end
    return events

def _targets(self):  # bếp rank 0, bàn rank 1
    return [(0, s) for s in self.stoves] + [(1, t) for t in self.tables]
```

Cuối `__init__` (commit khung) gọi `orders.on_load(self)` rồi `kitchen.on_load(self)` để mỗi lát tự suy ra trạng thái từ fixture.

### `chonoi/sim/quan_orders.py` — Chủ: Đặng Đức Minh (Lát 3)

| Hàm | Ai gọi | Làm gì | FR |
|---|---|---|---|
| `validate_scenario(block, tuning)` | `scenario.py` | Mâu thuẫn mức luật về khách/giữ chỗ → `raise BadInput` | FR-035 |
| `on_load(sim)` | `__init__` | Chuẩn hóa khách từ fixture (giữ chỗ, kiên nhẫn mặc định) | FR-035 |
| `available_stock(sim) -> dict` | L4, UI | Kho thực − tổng giữ chỗ | FR-032 |
| `pending_order(sim) -> dict \| None` | L4 | Khách `waiting`, chưa nấu, id nhỏ nhất | FR-041 |
| `consume_reserved(sim, customer)` | L4 | Trừ `reserved` khỏi `stock`, xóa `reserved`, đánh dấu `_cooking = True` | FR-041 |
| `customer_at_table(sim, table_id) -> dict \| None` | L4 | | FR-043 |
| `remove(sim, customer)` | L3, L4 | Xóa khách khỏi danh sách (khi đã trả tiền / rời) | |
| `tick_patience(sim, events)` | điều phối | Giảm kiên nhẫn khách `waiting` | FR-033 |
| `process_departures(sim, events) -> list[str]` | điều phối | Kiên nhẫn 0 → trả giữ chỗ, `customer_left`, `ledger.add_reputation(-0.5)`, `remove`. Trả id khách đã rời | FR-034 |
| `spawn_if_due(sim, events)` | điều phối | Lịch theo `sim.step_no`, chọn món bằng `sim.rng.get("customer_order")`, id bằng `sim.ids.new("C")` | FR-030..032 |
| `close_shift(sim, events)` | điều phối | Khách `waiting` rời, không phạt | FR-046 |

### `chonoi/sim/quan_kitchen.py` — Chủ: Phạm Quốc Huy (Lát 4)

| Hàm | Ai gọi | Làm gì | FR |
|---|---|---|---|
| `validate_scenario(block, tuning)` | `scenario.py` | Mâu thuẫn về bếp/tay/khách đang ăn → `raise BadInput` | FR-035 |
| `on_load(sim)` | `__init__` | Chuẩn hóa bếp/tay từ fixture | |
| `tick_stoves(sim, events)` | điều phối | Đếm ngược nấu → `dish_ready` | FR-041 |
| `tick_eating(sim, events)` | điều phối | Đếm ngược ăn → `paid` (`ledger.add_money`, tip → `add_reputation(+0.2)`), `orders.remove` | FR-043..045 |
| `interact(sim, target, events)` | điều phối | Bếp: nấu (`orders.pending_order` + `consume_reserved`) hoặc lấy món. Bàn: phục vụ. Không dùng được thì không làm gì | FR-040..044 |
| `discard_dish_for(sim, customer_id)` | điều phối | Bỏ món của khách đã rời (trên bếp → bếp trống; trên tay → tay trống) | FR-034 |
| `close_shift(sim, events)` | điều phối | Khách `eating` trả tiền ngay | FR-046 |

### Ma trận quyền ghi — buổi tối

| Trường | Được GHI bởi | Ghi chú |
|---|---|---|
| `pos`, `vel`, `_tgt`, `_ramp_left`, `step_no`, `time_left_ticks`, `done`, `reason` | bộ điều phối | |
| `stock` | L3 (`consume_reserved`) | L4 không trừ kho trực tiếp |
| `customers` (thêm/xóa) | L3 (`spawn_if_due`, `remove`) | L4 xóa **qua** `orders.remove` |
| `customer.patience_ticks`, `customer.reserved`, `customer._cooking` | L3 | |
| `customer.state` `waiting → eating`, `customer.eat_ticks`, `customer.tip` | L4 | Tạo khách ở `waiting` là L3 |
| `stoves[*]`, `hand` | L4 | |
| `money`, `earned`, `shift_earned`, `reputation` | `ledger.py` | L3 gọi `add_reputation(-0.5)`, L4 gọi `add_money`/`add_reputation(+0.2)` |

Hướng import cho phép: `quan_kitchen → quan_orders → ledger`, `quan_kitchen → ledger`, `* → pick`, `* → ids`. **Cấm** `quan_orders → quan_kitchen`. Bộ điều phối nối hai chiều (ví dụ `discard_dish_for`).

## 4. Lát 5 (UI) đọc gì

UI **chỉ đọc snapshot** qua `GET /state` (`chonoi/live.py`) và **chỉ gửi input** (`move`, `interact`, `catch`). Không tính luật ở client. Trường UI dựa vào nằm ở [`../data-model.md`](../data-model.md) §Snapshot. Trường chưa có thì client bỏ qua, nên UI làm song song được ngay từ đầu.
