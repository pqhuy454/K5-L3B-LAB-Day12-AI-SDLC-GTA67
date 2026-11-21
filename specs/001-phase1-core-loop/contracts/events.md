# Danh sách sự kiện Phase 1 (contract v1.0)

> Chủ: **Integrator**. Nguồn: docstring starter (`chonoi/sim/gather.py`, `quan.py`) + `docs/contracts/README.md`.
> Cột **Trạng thái**: ✅ = đã có trong code starter (đã biết chắc), ⚠️ = tên/payload **đề xuất**, PO phải đối chiếu Test Contract §E trước khi chủ lát code. Sai tên sự kiện là trượt test ẩn.
> Dòng event trong JSONL do runner bọc: `{"type":"event","tick":k+1,"phase":…,"name":…,"data":…}`. Lát chỉ `events.append((name, data))`.
> Thứ tự event trong một bước = thứ tự gọi hook trong [sim-hooks.md](sim-hooks.md). Không lát nào tự sắp lại.

## Buổi sáng (`gather`)

| Tên | `data` | Lát phát | Khi nào | Trạng thái |
|---|---|---|---|---|
| `node_regrown` | `{"node_id"}` | khung | `regrow_ticks` về 0 | ✅ |
| `dive` | `{"pos"}` | L1 | mặt nước → dưới nước (cuối bước) | ✅ tên, ⚠️ payload |
| `surface` | `{"pos"}` | L1 | dưới nước → mặt nước | ✅ tên, ⚠️ payload |
| `oxygen_empty` | `{}` | L1 | oxy từ dương về 0 | ✅ tên, ⚠️ payload |
| `choke` | `{"hp"}` | L1 | đủ 60 bước ngạt | ✅ tên, ⚠️ payload |
| `faint` | `{}` | L1 | Máu = 0 | ✅ tên, ⚠️ payload |
| `gather` | `{"node_id","kind"}` | L2 | hái thành công | ✅ tên, ⚠️ payload |
| `hold_full` | `{"need","free"}` | L2 | hái/bắt không đủ chỗ | ✅ tên, ⚠️ payload |
| `fish_caught` | `{"fish_id","kind","count"}` | L2 | bắt cả đàn | ✅ tên, ⚠️ payload |
| `gather_end` | `{"reason","inventory":{"items":{…}}}` | khung (`_finish`) | `docked` / `time` / `fainted` | ✅ |

## Buổi tối (`quan`)

| Tên | `data` | Lát phát | Khi nào | Trạng thái |
|---|---|---|---|---|
| `customer_arrived` | `{"customer_id","table_id","dish"}` | L3 | khách ngồi và gọi món | ⚠️ tên + payload (starter không nêu tên) |
| `no_dish` | `{}` | L3 | tới lượt nhưng không món nào nấu được | ✅ tên, ⚠️ payload |
| `customer_left` | `{"customer_id","reason"}` | L3 | hết kiên nhẫn / đóng ca | ✅ tên, ⚠️ payload |
| `cook_started` | `{"stove_id","dish","customer_id"}` | L4 | bắt đầu nấu | ✅ tên, ⚠️ payload |
| `dish_ready` | `{"stove_id","dish"}` | L4 | nấu xong | ✅ tên, ⚠️ payload |
| `dish_picked` | `{"stove_id","dish"}` | L4 | lấy món lên tay | ✅ tên, ⚠️ payload |
| `served` | `{"customer_id","dish","tip"}` | L4 | phục vụ đúng món | ✅ tên, ⚠️ payload |
| `paid` | `{"customer_id","amount","tip"}` | L4 | ăn xong / đóng ca | ✅ tên, ⚠️ payload |
| `quan_end` | `{"reason","money","earned","shift_earned","reputation"}` | khung | hết ca | ✅ |

## Quy tắc

- Mọi tên trong cột **Tên** phải là chuỗi viết y hệt (snake_case). Muốn đổi thì sửa bảng này trước.
- `data` là dict. Số thực được runner làm tròn 3 chữ số. Không đưa trường nội bộ `_xxx` vào `data`.
- Event không phát ở headless vì lý do trang trí (hiệu ứng, âm thanh). Phần trang trí đọc event ở client.
