# Movement and survival — kiểm chứng lát 1

- Thay đổi: oxy theo vị trí cuối bước; hồi ở mặt nước; ngạt tính từ bước oxy chạm 0; mất 1 HP sau mỗi `choke_interval_ticks`; ngất xóa giỏ trước `gather_end`. Theo `specs/001-phase1-core-loop/contracts/sim-hooks.md`, luật nằm trong `gather_survival.py`, giỏ có `free_slots`/`push_all`/`clear` trong `hold.py` để US2 dùng chung.
- Kiểm chứng ngày 2026-11-21 trên Windows, Python 3.13.2: `python -m unittest discover -s tests -v` — **35 test đạt** (gồm test mới và smoke Phase 1).
- `game.contract.json` gọi `python3`; máy thử nghiệm có alias Microsoft Store không chạy được. Khi chạy test, đặt bản sao `python.exe` tên `python3.exe` ở thư mục temp trước PATH. Không sửa contract hoặc test để vượt lỗi môi trường.
- Cần chạy lại bộ test từ commit được gắn tag trước khi nộp Phase 1.
