# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 | Payload chính xác của các event `dive`, `surface`, `oxygen_empty`, `choke`, `faint` trong PRD-0/Test Contract là gì? | Bản specification chỉ nêu tên event. Tạm phát `pos` cho chuyển vùng/oxy/ngất và `hp` cho choke; cần PO đối chiếu PRD-0 trước khi tag. | Chờ PO |
| 2 | 2026-11-21 10:15 | Schema trường `data` cho 3 sự kiện của Lát 2 (`gather`, `fish_caught`, `hold_full`) chưa liệt kê chi tiết trong [Quan_An_Cho_Noi_Specification.md](../Quan_An_Cho_Noi_Specification.md) | Giả định tạm khớp quy ước `node_id` của starter ([gather_actions.py](../chonoi/sim/gather_actions.py)):<br>- `gather`: `{"node_id", "kind", "count"}`<br>- `fish_caught`: `{"fish_id", "kind", "count"}`<br>- `hold_full`: `{"source": "node" \| "fish", "id", "kind", "needed", "free"}`<br>**Cần đối chiếu lại Test Contract v1.0 §E gốc.** | Member 2 (chờ PO xác nhận) |
| 3 | 2026-11-21 10:15 | Khi bấm `catch` (`Space`) dưới nước nhưng trượt (không có cá trong `2 m`) hoặc gặp `hold_full`, có kích hoạt hồi chiêu `catch_cd_ticks` (`0.5 s` = `30` tick) không? | Giả định tạm: chỉ đặt `catch_cd_ticks = 30` khi bắt trúng cá thành công; bấm trượt hoặc bị `hold_full` không bị khóa hồi chiêu.<br>**Cần đối chiếu lại Test Contract v1.0 §F gốc.** | Member 2 (chờ PO xác nhận) |

