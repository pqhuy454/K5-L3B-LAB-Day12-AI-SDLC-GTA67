# Retro nhóm

## Phase 2 (nhanh)
- **Điều tốt:**
  - Cả 5 thành viên chia lát rõ ràng theo đúng spec (US1 -> US5), code trong các module tách biệt (`gather_survival.py`, `gather_actions.py`, `quan_orders.py`, `quan_kitchen.py`).
  - Hợp đồng kiểm thử độc lập cho từng lát giúp viết unit test và mock fixture rất nhanh, không bị nghẽn chờ đợi nhau.
  - Giao diện web live tích hợp đồ họa sprite pack phong phú, hiệu ứng chuyển cảnh mượt.
- **Điều tệ:**
  - Khâu merge git còn bất cẩn: khi giải quyết xung đột nhánh (merge `main` vào `restaurant`), người gộp vô tình xóa mất định nghĩa hàm `step(self, inp)` trong `chonoi/sim/gather.py`.
  - Để sót code rác (`found[0]`) chưa dọn dẹp trong `live.py` gây lỗi 500/NameError khi load asset.
- **1 hành động cho Phase 3:**
  - Thiết lập quy tắc: Sau mỗi lần merge nhánh, bắt buộc chạy lại toàn bộ test suite (`python -m unittest discover -s tests -v`) và kiểm tra khởi động cả 2 mode `gather` và `quan` trước khi push lên nhánh chính.

---

## Phase 4 (cuối)
- **Rà lại hành động Phase 2: đã làm chưa? vì sao?**
  - Đã thực hiện nghiêm túc: toàn bộ test suite (36 unit/smoke tests) được chạy kiểm tra trước mỗi commit lớn.
- **Điều tốt / điều tệ:**
  - *Tốt:* Nhóm phối hợp ăn ý, tận dụng tối đa sức mạnh của AI để tạo boilerplate và test cases; sản phẩm hoàn thiện đúng hạn với đồ họa ấn tượng.
  - *Tệ:* Quá tin tưởng code do AI sinh ra ở lần đầu mà không đọc kỹ từng dòng diff, dẫn đến một số bug ngầm về biến cục bộ không tồn tại.
- **Số liệu:**
  - Số commit theo người: `pqhuy454` (8), `DMinh1102` (7), `TrGiaHuy1710-valid` (6), `thanh289` (3), `doananhhung` (4).
  - Cách đọc code của nhau: Review chéo thông qua Pull Request trên GitHub (`PR #1`, `PR #2`, `PR #3`) và đối chiếu với Test Contract.
  - Token tiêu thụ ước tính: ~310,000 tokens cho cả 5 thành viên.
- **Một lần AI sai và cách nhóm phát hiện:**
  - *Sự cố:* AI sinh logic bắt cá tự động gán hồi chiêu `catch_cd_ticks = 30` ngay cả khi bấm `Space` không trúng con cá nào.
  - *Cách phát hiện:* Unit test `test_catch_requires_underwater_and_miss_does_not_trigger_cooldown` trong bộ test của Lát 2 đã bắt được lỗi này ngay khi chạy kiểm thử tự động.
- **Nếu làm lại, đổi gì:**
  - Thiết lập Git hooks (pre-commit hook) chạy test tự động cục bộ để ngăn chặn triệt để việc commit code làm hỏng test hoặc lỗi cú pháp.
