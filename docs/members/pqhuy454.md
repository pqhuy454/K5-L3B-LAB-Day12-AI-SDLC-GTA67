# pqhuy454 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Giữ vai trò Integrator chính, quản trị repo và quản lý việc gộp các nhánh chức năng.
  - Triển khai Lát 4 (US4): Logic bếp nấu ăn, bưng bê món ăn trên tay, phục vụ tại bàn, tính tiền, tiền boa và uy tín ([5b6a49b](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/5b6a49b), [f6bce83](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/f6bce83), [c6e5675](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/c6e5675)).
  - Thiết lập và tinh chỉnh kịch bản tích hợp UI nhà hàng ([477a0c6](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/477a0c6), [f56f800](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/f56f800)).
- **Tôi đã review (kèm link):**
  - Đánh giá và merge các PR #1, PR #2, PR #3 từ các thành viên khác ([d73c142](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/d73c142), [22258e2](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/22258e2)).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - Khi AI sửa server HTTP `chonoi/live.py`, nó để lại biến `found` không tồn tại khiến server sập với `NameError` khi client tải ảnh. Tôi phát hiện khi kiểm tra log console lúc chạy lệnh `python3 -m chonoi.live`.
- **Điều tôi học được:**
  - Quá trình merge git cần sự cẩn trọng tối đa; không nên dựa dẫm hoàn toàn vào tự động giải quyết xung đột mà phải rà soát kỹ lưỡng diff từng file.
