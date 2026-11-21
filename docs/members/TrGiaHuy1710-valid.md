# TrGiaHuy1710-valid — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Đảm nhận vai trò QA lead, chịu trách nhiệm về giao diện người dùng, HUD và kiểm chứng hệ thống (US5).
  - Soạn thảo bộ đặc tả kỹ thuật chi tiết theo phương pháp Spec-Kit ([b4d262e](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/b4d262e)).
  - Xây dựng đồ họa giao diện cho cả 2 chế độ `gather` và `quan`, hiệu ứng lặn, bơi lội và chuyển cảnh dòng sông ([644065e](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/644065e), [d4a31f1](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/d4a31f1)).
- **Tôi đã review (kèm link):**
  - Phê duyệt PR #3 về tính năng chuyển cảnh dòng sông giữa buổi sáng và buổi tối ([22258e2](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/22258e2)).
  - Kiểm tra giao diện người dùng trên nhiều độ phân giải màn hình khác nhau.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI vẽ hình chữ nhật người chơi đè lên sprite và tính sai offset khung hình nhân vật pixel art khi di chuyển sang trái, dẫn đến nhân vật bị giật hình. Tôi phát hiện khi kiểm tra trực quan trên trình duyệt và đã căn chỉnh lại ma trận biến đổi canvas.
- **Điều tôi học được:**
  - Bằng chứng kiểm thử định lượng kết hợp với phản hồi trực quan từ UI là yếu tố cốt lõi để đảm bảo trải nghiệm người dùng hoàn chỉnh.
