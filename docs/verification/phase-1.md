# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| **US1.1–US1.5** (Bơi, oxy, ngạt, ngất, Máu) | Kiểm tra chuyển vùng `dive`/`surface`, giảm/hồi oxy theo độ sâu `d`, trừ Máu khi ngạt `choke`, ngất xóa sạch giỏ trước `gather_end` | [movement-survival.md](../proof/phase-1/movement-survival.md) & [test_smoke_p1.py](../../tests/test_smoke_p1.py) | **Đạt** (35/35 smoke tests pass) |
| **US1.6** (Sức chứa giỏ) | Chặn thêm món khi giỏ đủ 12/12 món | [movement-survival.md](../proof/phase-1/movement-survival.md) & `test_gather_slice2.py` | **Đạt** |
| **US2.1–US2.3** (Hái nút bông súng/điên điển) | Hái nút gần nhất ở mặt nước (`d <= 0.5`), tie-break theo `id_key`, thời gian mọc lại 20s (1200 ticks), báo `hold_full` khi giỏ đầy | [slice2-verification.md](../proof/phase-1/slice2-verification.md) | **Đạt** (13/13 unit tests pass) |
| **US2.4–US2.6** (Bắt đàn cá dưới nước) | Bắt cá dưới nước (`d > 0.5`), cá linh +3, cá lóc +1, kiểm tra hồi chiêu 0.5s (30 ticks), cấm bắt 1 phần | [slice2-verification.md](../proof/phase-1/slice2-verification.md) | **Đạt** |
| **US2.7–US2.9** (Cập bến & xuất kho) | Ưu tiên bến trước hái, tạo file kho JSON nguyên tử `catch.json`, `tick_limit` không xuất file | [slice2-verification.md](../proof/phase-1/slice2-verification.md) | **Đạt** |
| **US3.1–US3.6** (Khách đến, gọi món, giữ chỗ, kiên nhẫn) | Khách đến mỗi 15s (900 ticks) bắt đầu từ tick 120, kiểm tra kho khả dụng, giữ chỗ nguyên liệu, đếm lùi kiên nhẫn và trừ uy tín khi bỏ về | [test_quan_slice3.py](../../tests/test_quan_slice3.py) | **Đạt** |
| **US4.1–US4.9** (Bếp, nấu, bưng bê, phục vụ, tiền, uy tín) | Nấu ở bếp B1, chín sau `cook_s`, bưng trên tay tối đa 1 món, phục vụ tại bàn T1, tính tiền + boa khi kiên nhẫn >= 50%, đóng ca an toàn | [test_smoke_p1.py](../../tests/test_smoke_p1.py) | **Đạt** |
| **US5.1–US5.3** (HUD, đồ họa, kiểm chứng trực quan) | Canvas hiển thị đầy đủ thông số (oxy, Máu, giỏ, kho, tiền, uy tín), vẽ sprite pixel art người chơi, khách, món ăn, chuyển cảnh lặn -> quán | [graphics.md](../proof/phase-1/graphics.md) & [live.py](../../chonoi/live.py) | **Đạt** |

## Đánh giá ngắn
- **Yêu cầu đạt**: Toàn bộ vòng lặp cốt lõi từ lặn thu hoạch buổi sáng (`gather`) -> xuất kho -> nạp kho buổi tối mở quán (`quan`) hoạt động chính xác theo hợp đồng tất định (deterministic byte-for-byte). Cửa sổ chơi trực tiếp `chonoi.live` mượt mà với đầy đủ sprite đồ họa.
- **Yêu cầu chưa đạt / hạn chế**: Bộ test socket server trong `test_live.py` cần quyền mạng loopback trên môi trường sandbox; cần chú ý chạy trực tiếp hoặc cấp quyền khi test live server.
- **Điều cần chỉnh cho phase sau**: Tự động hóa kiểm tra xung đột merge trên git giữa các lát (đặc biệt các file dùng chung như `gather.py`, `quan.py`, `index.html`) để tránh sót hàm điều phối như sự cố mất hàm `step`.
