# Data Model — Phase 1

> Quy đổi: 1 s = 60 tick. Giá trị mặc định lấy từ `game.contract.json` (`tuning`). Trường bắt đầu bằng `_` là **nội bộ**, không xuất ra snapshot/JSONL.
> ⚠️ = tên trường đề xuất, đối chiếu Test Contract §E (snapshot) trước khi chốt.

## 1. Buổi sáng

### Người chơi (Út Sen) — trên `GatherSim`

| Trường | Kiểu | Mặc định | Ràng buộc | Chủ ghi | FR |
|---|---|---|---|---|---|
| `pos` | [x, d] float | `start_pos` = [2, 0] | x ∈ [0,100], d ∈ [0,30] | điều phối | FR-010 |
| `vel` | [vx, vd] | [0,0] | về 0 theo trục bị chặn | điều phối | FR-010 |
| `heading` (`heading_deg` ở snapshot) | độ | 0 | dương = hướng xuống | điều phối | |
| `oxygen_ticks` | int | 1 800 | [0, 1 800] | L1 | FR-012 |
| `zero_oxy_ticks` | int | 0 | [0, 59] sau mỗi bước | L1 | FR-013 |
| `hp` | int | 3 | [0, 3] | L1 | FR-014 |
| `catch_cd_ticks` | int | 0 | ≥ 0, đặt 30 khi bắt được | điều phối giảm, L2 đặt | FR-023 |
| `invuln_ticks` | int | 0 | chưa dùng ở Phase 1 | điều phối | |

### Giỏ — `sim.hold`

- Mảng id nguyên liệu theo thứ tự nhặt (cuối = mới nhất), `len ≤ hold_capacity (12)`.
- Chỉ `hold.py` ghi (FR-015). Snapshot: `hold`, `hold_count`, `hold_capacity`.

### Nút hái — `sim.nodes[]`

| Trường | Ràng buộc |
|---|---|
| `id` | duy nhất, sắp theo `id_key` |
| `kind` | `bong_dien_dien` \| `bong_sung` |
| `pos` | d = 0 (mặt nước) |
| `regrow_ticks` | 0 = sẵn sàng (`ready` ở snapshot). Hái xong đặt 1 200 |

### Đàn cá — `sim.fish[]`

| Trường | Ràng buộc |
|---|---|
| `id`, `kind` (`ca_linh` \| `ca_loc`), `pos` (d > 0,5), `heading_deg` | đứng yên ở Phase 1. Bắt xong thì xóa khỏi danh sách |

Sản lượng: `fish_yield` = {ca_linh: 3, ca_loc: 1}.

### Kho (inventory) — hợp đồng giữa hai tiến trình

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- Chỉ khóa gốc `items`. Chỉ 4 id nguyên liệu, số nguyên ≥ 0. Bỏ mục 0 khi ghi, khóa sắp theo bảng chữ cái.
- Ghi một lần, nguyên tử, khi `gather_end`. Phần này khung đã có sẵn (`chonoi/inventory.py`), **không ai sửa**.

### Chuyển trạng thái buổi sáng

```text
playing ──interact trong bến──────▶ finished(docked)   kho = giỏ
playing ──time_left = 0───────────▶ finished(time)     kho = giỏ
playing ──hp = 0 (ngạt)───────────▶ finished(fainted)  kho = {}
playing ──đạt --ticks trước───────▶ (end reason tick_limit)  KHÔNG ghi kho
```

## 2. Buổi tối

### Người chơi / tay — trên `QuanSim`

| Trường | Kiểu | Ràng buộc | Chủ ghi |
|---|---|---|---|
| `pos`, `vel` | [x, z] | x ∈ [0,16], z ∈ [0,10] | điều phối |
| `hand` | `null` hoặc `{"dish","customer_id"}` ⚠️ | tối đa 1 món | L4 |
| `step_no` | int | số bước đã chạy trong lượt (dùng cho lịch khách) ⚠️ đối chiếu mốc "tick 120" | điều phối |

### Kho buổi tối

- `stock`: kho thực (dict nguyên liệu → số). Chỉ L3 ghi (qua `consume_reserved`).
- Kho khả dụng = `stock − Σ customer.reserved` (`orders.available_stock`). UI hiển thị **kho khả dụng** (FR-051).

### Khách / đơn — `sim.customers[]`

| Trường | Kiểu | Chủ ghi | Ghi chú |
|---|---|---|---|
| `id` | "C1", "C2"… | L3 | `ids.new("C")` |
| `table_id` | id bàn | L3 | bàn phải tồn tại, mỗi bàn ≤ 1 khách |
| `dish` ⚠️ | id món | L3 | chọn đều trong món nấu được |
| `state` ⚠️ | `waiting` \| `eating` | L3 tạo `waiting`, L4 chuyển `eating` | |
| `patience_ticks` ⚠️ | int, 3 600 → 0 | L3 | chỉ giảm khi `waiting` |
| `reserved` | dict nguyên liệu → số | L3 | rỗng sau khi bắt đầu nấu |
| `eat_ticks` ⚠️ | int, 600 → 0 | L4 | chỉ khi `eating` |
| `tip` ⚠️ | int | L4 | tính lúc phục vụ |
| `_cooking` | bool | L3 | nội bộ: đã bắt đầu nấu |

Fixture mâu thuẫn → mã 2 (FR-035): khách `waiting` có `reserved` vượt kho; `eating` mà thiếu `eat_ticks`; hai khách cùng bàn; bàn lạ; trạng thái lạ.

### Bếp — `sim.stoves[]`

| Trường | Giá trị | Chủ ghi |
|---|---|---|
| `id`, `pos` | B1 @ [2, 8] | khung |
| `state` | `idle` \| `cooking` \| `ready` | L4 |
| `dish` | id món hoặc null | L4 |
| `customer_id` ⚠️ | khách mà món thuộc về | L4 |
| `cook_ticks_left` | đếm về 0 → `ready` | L4 |
| `ready_ticks` | đếm thời gian chín (cháy tắt ở Phase 1: `burn_s = null`) | L4 |

### Bàn — `sim.tables[]`

`id`, `pos` (T1 @ [9, 2]). Snapshot thêm `customer_id` (suy ra từ khách, khung đã làm).

### Sổ quán

`money`, `earned`, `shift_earned` (int, nghìn đồng), `reputation` (float, [0, 5], bắt đầu 3). Chỉ `ledger.py` ghi. `score = earned + 100 × floor(reputation)` do runner tính.

### Chuyển trạng thái khách

```text
(cơ hội đến, có bàn trống, có món) ──▶ waiting  [giữ chỗ nguyên liệu]
waiting ──cook_started──▶ waiting(_cooking)      [tiêu nguyên liệu, reserved = {}]
waiting ──served (đúng món trên tay)──▶ eating   [tip tính lúc này]
eating ──eat_ticks = 0──▶ paid → xóa             [+tiền, tip>0 → +0,2 uy tín]
waiting ──patience = 0──▶ left → xóa             [−0,5 uy tín, trả reserved còn lại, bỏ món]
hết ca: eating ──▶ paid ngay; waiting ──▶ left (không phạt)
```

### Chuyển trạng thái bếp

```text
idle ──interact + pending_order──▶ cooking ──cook_ticks_left = 0──▶ ready ──interact, tay trống──▶ idle
cooking/ready ──khách của món rời đi──▶ idle (bỏ món)
```

## 3. Snapshot — trường UI (Lát 5) đọc

| Mode | Trường |
|---|---|
| chung | `tick`, `time_left_ticks`, `money`, `earned`, `reputation`, `score`, `state` |
| gather | `player.{pos, oxygen_ticks, oxygen_max_ticks, hp, hp_max, at_surface}`, `hold`, `hold_count`, `hold_capacity`, `nodes[].ready`, `fish[]` |
| quan | `player.pos`, `stock` ⚠️ (kho thực; UI tự trừ `reserved` để ra kho khả dụng), `hand`, `stoves[]`, `tables[]`, `customers[]` |
