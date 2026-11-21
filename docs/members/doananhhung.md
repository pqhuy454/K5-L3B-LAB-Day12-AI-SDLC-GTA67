# doananhhung — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Giữ vai trò Scrum/Release, theo dõi tiến độ các lát và đảm bảo chất lượng tích hợp.
  - Xây dựng Lát 2 (US2): Cơ chế hái nút bông súng, bắt cá dưới nước và xuất file kho an toàn ([60e8a23](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/60e8a23), [ab032bf](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/ab032bf)).
  - Bổ sung 13 ca kiểm thử biên và smoke test 2 tiến trình ([0049504](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/0049504)) cùng tài liệu xác minh ([6024ba2](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/6024ba2)).
- **Tôi đã review (kèm link):**
  - Review PR #2 của Trần Duy Thành về module sinh tồn `gather_survival.py` ([PR #2](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/pull/2)).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI thiết lập kích hoạt thời gian hồi chiêu `catch_cd_ticks` bất kể người chơi bắt trúng hay trượt. Nhờ viết test tự động trước (`test_catch_requires_underwater_and_miss_does_not_trigger_cooldown`), lỗi này đã bị phát hiện ngay lập tức và được khắc phục.
- **Điều tôi học được:**
  - Viết test kiểm thử biên theo hướng Test-Driven Development (TDD) là cách an toàn và tin cậy nhất khi làm việc cùng các mô hình AI.
