# Đồ họa buổi sáng — kiểm chứng

- Giao diện đọc sprite từ `assets/SpearFishing Assets Pack` và `assets/Restaurant Assets Pack` qua danh sách đường dẫn cố định trong máy chủ live; đây là lý do sửa `chonoi/live.py` của starter. Logic headless không thay đổi.
- Kiểm thử ngày 2026-11-21 trên Windows, Python 3.13.2: `python -m unittest discover -s tests -v` — **35 test đạt**. Dùng shim `python3.exe` trong thư mục temp để chạy lệnh `headless_cmd` trên máy có alias Microsoft Store.
- Mở game live ở chế độ `gather` tại cổng 8767: bảy sprite tải thành công; canvas vẽ người lặn, hai loại cá, rong, san hô, bong bóng và đáy sông. Kiểm tra ảnh render trong trình duyệt ở kích thước 1280 × 960.
- Mở game live ở chế độ `quan` tại cổng 8766: sprite bàn, bếp và đèn dây tải thành công và được vẽ trên canvas. Route ảnh được test bằng HTTP trong `test_live.py`.
- Giấy phép của asset pack cần được nhóm đối chiếu với yêu cầu repo public trước khi phát hành.
