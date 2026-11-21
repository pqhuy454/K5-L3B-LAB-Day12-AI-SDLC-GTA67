# DMinh1102 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Đảm nhận vai trò Co-Integrator, thiết kế kịch bản mở quán buổi tối.
  - Triển khai Lát 3 (US3): Quản lý vòng đời khách hàng, lịch đến của khách, chọn món từ kho khả dụng và giữ chỗ nguyên liệu ([9208d67](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/9208d67), [7f48bb8](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/7f48bb8), [3d72a17](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/3d72a17)).
  - Tích hợp tài nguyên sprite nhân vật và hoạt ảnh quay 4 hướng ([408607f](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/408607f), [7337e7f](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/7337e7f)).
- **Tôi đã review (kèm link):**
  - Review nhánh `restaurant` của Phạm Quốc Huy về cơ chế tương tác bếp và phục vụ bàn ([f6bce83](https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67/commit/f6bce83)).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI sử dụng hàm ngẫu nhiên tiêu chuẩn của Python thay vì generator hạt giống `Streams` từ khung contract, làm mất tính tất định. Tôi nhận ra khi chạy thử nghiệm 2 lượt cùng seed nhưng kết quả trả về món gọi khác nhau.
- **Điều tôi học được:**
  - Khi lập trình game mô phỏng tất định, mọi nguồn ngẫu nhiên và thời gian đều phải đi qua luồng điều khiển seed tập trung.
