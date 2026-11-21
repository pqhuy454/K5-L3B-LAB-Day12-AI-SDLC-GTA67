# thanh289 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Đảm nhận vai trò Product Owner (PO), duy trì hợp đồng và tài liệu [clarify.md](../clarify.md).
  - Triển khai Lát 1 (US1): Vòng lặp sinh tồn dưới nước, tính toán lượng oxy tiêu thụ theo độ sâu, cơ chế ngạt nước và ngất xỉu khi hết Máu (`gather_survival.py`, commit [c30afe8](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/c30afe8)).
  - Hợp nhất nhánh và đồng bộ với nhánh chính ([6a35723](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/6a35723), [06462d1](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/06462d1)).
- **Tôi đã review (kèm link):**
  - Review PR #1 của Đoàn Anh Hùng về hành động hái và bắt cá ([PR #1](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/pull/1)).
  - Đối chiếu các giả định sự kiện Lát 2 với Test Contract v1.0.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI sinh mã tính toán trạng thái oxy dựa trên vị trí đầu bước thay vì vị trí cuối bước sau khi dịch chuyển. Tôi phát hiện điều này khi so sánh kết quả trace log với kịch bản smoke test trong spec và đã sửa lại thứ tự thực thi.
- **Điều tôi học được:**
  - Tách biệt rõ ràng giữa logic mô phỏng cốt lõi và giao diện giúp các thành viên phát triển độc lập mà không bị gián đoạn.
