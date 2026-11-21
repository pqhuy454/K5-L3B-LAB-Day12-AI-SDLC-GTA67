# Bằng chứng kiểm chứng Lát 2 — Phase 1 (Gathering & Inventory)

- **Nhánh:** `feat/slice2-gather-actions`
- **Phạm vi:** Hái nút mặt nước, bắt đàn cá dưới nước, ưu tiên cập bến, xuất và đọc file kho giữa 2 tiến trình.
- **Tệp triển khai:** [gather_actions.py](../../../chonoi/sim/gather_actions.py), [gather.py](../../../chonoi/sim/gather.py), [test_gather_slice2.py](../../../tests/test_gather_slice2.py).
- **Giả định đang chờ đối chiếu Test Contract v1.0 gốc:** Xem mục #1 và #2 trong [clarify.md](../../clarify.md).

---

## 1. Kết quả chạy bộ kiểm thử tự động

Lệnh thực thi trên Windows PowerShell:

```powershell
$env:PYTHONPATH="tests;."
python -m unittest tests.test_gather_slice2 tests.test_python_starter_units tests.test_live tests.test_team_check -v
```

Kết quả đo thực tế: **25/25 test đạt (`OK`, 2.488s)**, gồm toàn bộ **13/13 test mới của Lát 2**:

| Hạng mục kiểm chứng | Ca kiểm thử trong `test_gather_slice2.py` | Kết quả |
| :--- | :--- | :--- |
| Hái nút & mọc lại 20 s (`1200` tick) | `test_harvest_at_surface_collects_and_regrows` | Pass |
| Điều kiện mặt nước (`d <= 0.5`) & biên bán kính (`2.0 m`) | `test_harvest_requires_surface_and_radius_boundaries` | Pass |
| Chọn nút `ready` gần nhất & tie-break `id_key` (`N2 < N10`) | `test_harvest_nearest_and_numeric_id_tiebreak` | Pass |
| Giỏ đầy khi hái giữ nguyên nút `ready`, không lặp khi giữ phím | `test_harvest_hold_full_keeps_node_ready_and_no_repeat_when_held` | Pass |
| Bắt `ca_linh` (+3) & `ca_loc` (+1), giữ thứ tự giỏ LIFO | `test_catch_underwater_ca_linh_and_ca_loc_lifo_order` | Pass |
| Hồi chiêu `0.5 s` (`30` tick): chặn ở tick 29, mở ở tick 30 | `test_catch_blocked_on_tick_29_and_allowed_on_tick_30` | Pass |
| Yêu cầu dưới nước (`d > 0.5`), trượt không đặt cooldown | `test_catch_requires_underwater_and_miss_does_not_trigger_cooldown` | Pass |
| Tie-break đàn cá theo `id_key` (`F2 < F10`) | `test_catch_numeric_id_tiebreak` | Pass |
| Cấm bắt cá một phần & không fallback sang đàn cá xa hơn | `test_catch_forbids_partial_and_no_fallback_to_farther_school` | Pass |
| Ưu tiên cập bến trước hái nút và bắt cá | `test_dock_takes_priority_over_harvest_and_catch` | Pass |
| Smoke test 2 tiến trình bắt buộc (`Quan_An_Cho_Noi_Specification.md` §8) | `test_mandatory_spec_two_process_smoke_transfer` | Pass |
| Luồng đầu-cuối: hái + bắt cá + cập bến + xuất/đọc kho + tất định từng byte | `test_end_to_end_harvest_catch_dock_transfer_and_determinism` | Pass |
| `tick_limit` không tạo file kho; hết giờ (`time`) ghi đúng vật phẩm đã hái | `test_tick_limit_does_not_write_inventory_and_time_writes_harvested_items` | Pass |

---

## 2. Kết quả chạy trực tiếp Smoke Test 2 tiến trình (CLI)

Fixture: `dock.json` = `{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}`, `dock-inputs.json` = `{"frames":[{"tick":0,"interact":true}]}`.

Lệnh thực thi:

```bash
python -m chonoi.headless --mode gather --seed 42 --scenario dock.json --inputs dock-inputs.json --ticks 1 --out gather.jsonl --inventory-out catch.json
python -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
```

Đầu ra quan sát thực tế:

- Mã thoát tiến trình `gather`: `0`
- Mã thoát tiến trình `quan`: `0`
- Nội dung `catch.json`:

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

- Sự kiện kết thúc trong `gather.jsonl`:

```json
{"type":"event","tick":1,"phase":"gather","name":"gather_end","data":{"reason":"docked","inventory":{"items":{"bong_sung":2,"ca_loc":1}}}}
```

- Snapshot tick 0 trong `quan.jsonl` (trích trường `stock`):

```json
"stock":{"bong_sung":2,"ca_loc":1}
```

---

## 3. Ranh giới chưa kiểm chứng trên máy cục bộ

- Bộ test hộp đen mặc định [test_smoke_p1.py](../../../tests/test_smoke_p1.py) gọi lệnh `python3 -m chonoi.headless` từ [game.contract.json](../../../game.contract.json) nên báo `FileNotFoundError` trên môi trường Windows hiện tại chưa có alias `python3` trong `PATH` (không sửa `game.contract.json` để giữ tương thích CI Linux).
- Chưa kiểm thử tích hợp với nhánh `fainted` của Lát 1 vì logic oxy/ngạt/ngất thuộc phạm vi Member 1 chưa được ghép vào nhánh này.
