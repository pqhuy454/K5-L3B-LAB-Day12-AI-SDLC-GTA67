# Feature Specification: Phase 1 — Vòng lõi Lặn & Hái → Kho → Mở Quán (nhóm 5 người)

**Feature Branch**: `001-phase1-core-loop`

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "Đọc repo K5-L3B-LAB-Day12-AI-SDLC-GTA67, viết spec kỹ hơn với 5 thành viên, và lưu ý code như nào để tránh bị conflict khi merge."

> Nguồn yêu cầu: `Quan_An_Cho_Noi_Specification.md` (bản tóm tắt PRD-0 + Test Contract v1.0), `game.contract.json` (preset), `TEAM.md` (phân vai). Khi spec này và **Test Contract v1.0** khác nhau ở chi tiết giao thức (tên sự kiện, trường snapshot, thứ tự trong một bước), **Test Contract thắng**; PO ghi chênh lệch vào `docs/clarify.md`.
>
> Spec chỉ nói **cái gì** và **vì sao**. Cách tổ chức mã, chia file và quy tắc tránh conflict khi merge nằm ở [`plan.md`](plan.md).

**Quy đổi thời gian dùng trong spec**: game chạy 60 bước (tick) mỗi giây. 1 s = 60 tick; 0,5 s = 30 tick; 10 s = 600 tick; 15 s = 900 tick; 20 s = 1 200 tick; 30 s = 1 800 tick; 60 s = 3 600 tick; 180 s = 10 800 tick.

## Phân công theo câu chuyện người dùng

| Câu chuyện | Ưu tiên | Chủ (owner) | Người dự phòng | Phụ thuộc |
|---|---|---|---|---|
| US1 — Lặn sống sót (bơi, oxy, ngạt, ngất, giỏ) | P1 | Trần Duy Thành (`thanh289`) | Đoàn Anh Hùng | Không (di chuyển đã có sẵn) |
| US2 — Hái, bắt cá, cập bến, xuất kho | P1 | Đoàn Anh Hùng (`doananhhung`) | Trần Duy Thành | Dùng "giỏ" của US1 (quy ước dùng chung, chốt từ đầu) |
| US3 — Khách đến, gọi món, giữ chỗ, kiên nhẫn | P2 | Đặng Đức Minh (`DMinh1102`) | Phạm Quốc Huy | Đọc kho từ US2 (chỉ cần file kho hợp lệ) |
| US4 — Nấu, bưng, phục vụ, thu tiền, uy tín | P2 | Phạm Quốc Huy (`pqhuy454`) | Đặng Đức Minh | Dùng đơn hàng và giữ chỗ của US3 (quy ước dùng chung, chốt từ đầu) |
| US5 — Chơi được qua HUD + bằng chứng kiểm chứng | P3 | Trịnh Gia Huy (`TrGiaHuy1710-valid`) | Lát đang chậm | Đọc trạng thái do US1–US4 công bố |

Mỗi câu chuyện **kiểm thử được độc lập** nhờ fixture (scenario) dựng sẵn trạng thái. Ví dụ US4 kiểm được bằng khách dựng sẵn mà không cần US3 hoàn chỉnh. Đây là điều kiện để 5 người làm song song.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lặn sống sót dưới sông (Priority: P1)

Út Sen bơi trong mặt cắt dòng sông (nhìn ngang). Ở mặt nước thì hồi oxy, lặn xuống thì mất oxy. Hết oxy mà vẫn ở dưới nước thì bị ngạt và mất Máu. Hết Máu thì ngất: buổi sáng kết thúc và mất toàn bộ giỏ.

**Why this priority**: Đây là áp lực chính của buổi sáng. Không có oxy và ngất thì buổi sáng không có rủi ro, và luật "ngất thì kho rỗng" của Test Contract không kiểm được.

**Independent Test**: Dựng người chơi ở độ sâu cố định với oxy cho trước, giữ yên hoặc bơi lên rồi đọc oxy, Máu, sự kiện và lý do kết thúc. Không cần nút hái hay cá.

**Acceptance Scenarios**:

1. **Given** Út Sen ở mặt nước (d ≤ 0,5) với oxy đầy 1 800, **When** bơi xuống để cuối bước d > 0,5, **Then** phát đúng một sự kiện `dive` và oxy giảm 1 mỗi bước ở dưới nước.
2. **Given** Út Sen dưới nước với oxy 100, **When** bơi lên để cuối bước d ≤ 0,5, **Then** phát `surface`, rồi mỗi bước ở mặt nước oxy tăng 6 và không vượt 1 800.
3. **Given** Út Sen dưới nước với oxy 1 và Máu 3, đứng yên, **When** chạy bước 1, **Then** oxy về 0, phát `oxygen_empty` một lần và bộ đếm ngạt = 1 (bước chạm 0 được tính).
4. **Given** như trên, **When** chạy tiếp tới bước 60, **Then** phát `choke`, Máu còn 2 và bộ đếm ngạt quay về 0. Tới bước 120 còn 1 Máu. Tới bước 180 phát `choke` lần ba, Máu = 0, phát tiếp `faint` rồi `gather_end` với lý do `fainted` và kho `{"items":{}}`.
5. **Given** Út Sen dưới nước, oxy 0, bộ đếm ngạt 30, **When** bơi lên mặt nước, **Then** bộ đếm ngạt về 0 và không mất Máu.
6. **Given** giỏ có 12/12 món, **When** có hành động thêm món, **Then** giỏ không vượt 12 (luật từ chối thuộc US2, nhưng sức chứa và thứ tự nhặt thuộc US1).

---

### User Story 2 - Hái rau, bắt cá, cập bến và chuyển kho (Priority: P1)

Ở mặt nước, Út Sen hái bông điên điển hoặc bông súng. Dưới nước, cô bắt nguyên một đàn cá (cá linh được 3, cá lóc được 1). Về bến thì giỏ thành kho cho buổi tối. Buổi tối là một lần chạy riêng, đọc kho này.

**Why this priority**: Đây là nửa đầu của vòng lõi, và cũng là yêu cầu bắt buộc "chuyển kho giữa hai tiến trình riêng" của Phase 1. Không có kho thì buổi tối không có gì để nấu.

**Independent Test**: Dựng nút hái hoặc đàn cá cạnh người chơi, bấm `interact` hoặc `catch`, rồi đọc giỏ và sự kiện. Cập bến ở bước 0 với giỏ dựng sẵn rồi so file kho, đúng ví dụ smoke test hai tiến trình.

**Acceptance Scenarios**:

1. **Given** Út Sen ở mặt nước, cách nút `N1` (sẵn sàng) 1,5 m và cách `N2` 1,9 m, **When** bấm `interact`, **Then** hái `N1` (gần nhất), giỏ thêm 1 món đúng loại, phát `gather` và `N1` hết sẵn sàng trong 1 200 bước rồi phát `node_regrown`.
2. **Given** hai nút sẵn sàng cách đều nhau, **When** bấm `interact`, **Then** hái nút có id nhỏ hơn (F2 đứng trước F10).
3. **Given** giỏ đầy 12/12 ở mặt nước cạnh nút sẵn sàng, **When** bấm `interact`, **Then** phát `hold_full`, giỏ không đổi và nút vẫn sẵn sàng.
4. **Given** Út Sen dưới nước cách đàn cá linh 1,8 m, giỏ còn ≥ 3 chỗ và hồi chiêu = 0, **When** bấm `catch`, **Then** giỏ thêm 3 `ca_linh`, đàn cá biến mất, phát `fish_caught` và hồi chiêu đặt 30 bước.
5. **Given** giỏ còn 2 chỗ, **When** bắt đàn cá linh (cần 3 chỗ), **Then** phát `hold_full`, không bắt một phần và đàn cá còn nguyên.
6. **Given** Út Sen ở mặt nước, **When** bấm `catch`, **Then** không có gì xảy ra (chỉ bắt được dưới nước).
7. **Given** giỏ `[ca_loc, bong_sung, bong_sung]` và Út Sen trong bán kính bến 3 m, **When** bấm `interact` ở bước 0, **Then** phát `gather_end` lý do `docked`, file kho đúng `{"items":{"bong_sung":2,"ca_loc":1}}`, và lần chạy buổi tối đọc file này có snapshot bước 0 với `stock` giống hệt.
8. **Given** Út Sen trong vùng bến và đồng thời cạnh nút hái, **When** bấm `interact`, **Then** cập bến được ưu tiên trước hái.
9. **Given** lần chạy dừng vì đạt giới hạn số bước trước khi buổi sáng kết thúc, **When** lần chạy xong, **Then** file kho đích không được tạo hoặc ghi đè.

---

### User Story 3 - Khách đến, gọi món và chờ (Priority: P2)

Quán mở tối. Khách đến theo lịch cố định, ngồi bàn trống và gọi một món nấu được từ kho. Nguyên liệu cho món đó được giữ chỗ ngay. Khách chờ được tối đa 60 giây, quá thì bỏ đi và quán mất uy tín.

**Why this priority**: Đây là nửa sau của vòng lõi, nhưng chỉ có ý nghĩa khi có kho (US2) và có người phục vụ (US4). Phần "giữ chỗ" quyết định tính đúng của kinh tế quán.

**Independent Test**: Chạy buổi tối với kho dựng sẵn và không có input, rồi đọc thời điểm khách đến, món chọn, phần giữ chỗ, kho khả dụng, kiên nhẫn giảm dần và sự kiện bỏ đi.

**Acceptance Scenarios**:

1. **Given** kho `{"ca_loc":1}` và bàn `T1` trống, **When** tới bước 120, **Then** một khách mới ngồi `T1`, gọi `ca_loc_nuong_trui` (món duy nhất nấu được), giữ chỗ `ca_loc ×1`, và kho khả dụng còn 0 `ca_loc`.
2. **Given** kho đủ cho cả ba món, **When** khách đến, **Then** món được chọn đều ngẫu nhiên trong các món nấu được. Cùng seed thì luôn cùng món.
3. **Given** kho rỗng (hoặc mọi nguyên liệu đã bị giữ chỗ), **When** tới lượt khách đến, **Then** phát `no_dish` và không có khách ngồi.
4. **Given** khách đang chờ với kiên nhẫn 3 600, **When** 3 600 bước trôi qua mà chưa được phục vụ, **Then** phát `customer_left`, uy tín giảm 0,5 (không dưới 0), phần nguyên liệu giữ chỗ chưa nấu được trả lại kho khả dụng, và món đã nấu cho khách này (trên bếp hoặc trên tay) bị bỏ.
5. **Given** khách bỏ đi sau khi món của họ đã bắt đầu nấu, **When** khách rời, **Then** nguyên liệu đã tiêu khi nấu **không** được hoàn lại.
6. **Given** lịch khách, **When** chạy hết ca 10 800 bước, **Then** cơ hội khách đến rơi đúng vào các bước 120, 1 020, 1 920, … (mỗi 900 bước).

---

### User Story 4 - Nấu, bưng, phục vụ và thu tiền (Priority: P2)

Út Sen tới bếp bắt đầu nấu món khách gọi. Món chín thì lấy lên tay (mỗi lần cầm 1 món) rồi mang tới đúng bàn. Khách ăn 10 giây rồi trả tiền, kèm tiền boa nếu còn kiên nhẫn. Tiền boa tăng uy tín.

**Why this priority**: Đây là nơi sinh tiền và điểm. Nó phụ thuộc vào đơn hàng của US3, nhưng kiểm thử độc lập được bằng khách dựng sẵn trong fixture.

**Independent Test**: Dựng bếp, bàn, một khách đang chờ có giữ chỗ và người chơi cạnh bếp. Gửi chuỗi `interact` (nấu, lấy món, đi tới bàn, phục vụ) rồi đọc trạng thái bếp, tay, tiền, uy tín và điểm.

**Acceptance Scenarios**:

1. **Given** người chơi cạnh bếp `B1` trống, tay trống, có khách đang chờ `ca_loc_nuong_trui`, **When** bấm `interact`, **Then** phát `cook_started`, nguyên liệu giữ chỗ bị tiêu khỏi kho, và sau 360 bước bếp chuyển sang "chín" và phát `dish_ready`.
2. **Given** bếp có món chín và tay trống, **When** bấm `interact` tại bếp, **Then** phát `dish_picked`, tay cầm món đó và bếp trống trở lại.
3. **Given** tay cầm món đúng của khách ở `T1`, **When** bấm `interact` tại `T1`, **Then** phát `served`, tay trống và khách chuyển sang "đang ăn" trong 600 bước, sau đó phát `paid`.
4. **Given** lúc phục vụ khách còn ≥ 50% kiên nhẫn (≥ 1 800 bước, tính sau khi đã giảm của bước đó), **When** khách trả tiền, **Then** tiền = giá + floor(giá × 0,2) (ví dụ lẩu 120 → 144) và uy tín +0,2 tại lúc trả tiền (không vượt 5).
5. **Given** lúc phục vụ khách còn < 50% kiên nhẫn, **When** khách trả tiền, **Then** chỉ nhận đúng giá, không boa và uy tín không đổi.
6. **Given** khách còn đúng 1 bước kiên nhẫn, **When** phục vụ ở bước kiên nhẫn chạm 0, **Then** phục vụ hợp lệ và khách không bỏ đi.
7. **Given** người chơi cách bếp 1,0 m và cách bàn 1,0 m, **When** bấm `interact`, **Then** chọn bếp (cùng khoảng cách thì bếp trước bàn, rồi theo id). Nếu không làm gì được với bếp đó thì **không** chuyển sang bàn.
8. **Given** hết ca khi có khách đang ăn và khách đang chờ, **When** đồng hồ về 0, **Then** khách đang ăn trả tiền ngay, khách đang chờ rời đi **không** bị trừ uy tín, và phát `quan_end` cuối cùng.
9. **Given** bất kỳ trạng thái nào, **When** đọc điểm, **Then** điểm = tiền kiếm được + 100 × floor(uy tín).

---

### User Story 5 - Chơi được bằng mắt và có bằng chứng (Priority: P3)

Người chơi mở cửa sổ chơi thử, nhìn HUD là hiểu tình hình (oxy, Máu, giỏ, kho, đơn, kiên nhẫn, bếp, tay, tiền, uy tín) và nhận phản hồi rõ khi hành động thành công hay thất bại. Giảng viên mở `docs/verification/phase-1.md` và thấy từng tiêu chí có bằng chứng thật từ commit được gắn tag.

**Why this priority**: Phần chấm tự động dựa vào lõi (US1–US4). HUD và bằng chứng chiếm điểm "chất lượng sản phẩm", "kiểm chứng" và "demo", nhưng chỉ có giá trị khi lõi đã chạy.

**Independent Test**: Mở cửa sổ chơi ở cả hai chế độ, đối chiếu từng mục HUD bắt buộc. Chạy kịch bản kiểm chứng trong `quickstart.md` và đối chiếu bảng truy vết.

**Acceptance Scenarios**:

1. **Given** buổi sáng đang chơi, **When** nhìn màn hình, **Then** thấy thời gian còn lại, oxy, Máu, giỏ (số món/sức chứa và nội dung).
2. **Given** buổi tối đang chơi, **When** nhìn màn hình, **Then** thấy thời gian còn lại, kho khả dụng, đơn của khách, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín.
3. **Given** người chơi giữ phím E hoặc Space, **When** giữ nhiều bước liền, **Then** hành động chỉ xảy ra một lần (kích hoạt khi chuyển từ nhả sang nhấn).
4. **Given** giỏ đầy, thiếu nguyên liệu, món chín hoặc khách bỏ đi, **When** sự kiện xảy ra, **Then** có phản hồi nhìn thấy được.
5. **Given** tag `phase-1`, **When** người chấm checkout tag đó, **Then** mọi tiêu chí trong bảng truy vết có bằng chứng tái tạo được từ đúng commit đó.

---

### Edge Cases

- **Cùng một bước có nhiều việc**: thứ tự xử lý trong một bước theo Test Contract §F. Buổi sáng: đồng hồ và mọc lại → di chuyển → đổi vùng (lặn/nổi) → oxy, ngạt, ngất (ngất thì dừng bước) → `interact` (bến trước, rồi hái) → `catch` → hết giờ.
- **Ngất và hết giờ cùng bước**: ngất xét trước, buổi sáng kết thúc với lý do `fainted` và kho rỗng.
- **Cập bến và hết giờ cùng bước**: `interact` được xét trước hết giờ, nên lý do là `docked`.
- **Nút đang mọc lại gần hơn nút sẵn sàng**: chỉ xét nút sẵn sàng.
- **Đối tượng gần nhất không dùng được** (bếp đang nấu, bàn không có khách, món không khớp): không làm gì, không chuyển sang đối tượng khác.
- **Bấm `interact` tại bàn khi tay cầm món của khách khác**: không phục vụ, tay giữ nguyên.
- **Bàn duy nhất đang có khách khi tới lượt khách mới**: không có khách mới (giả định, xem Assumptions).
- **Kho có nguyên liệu nhưng đã bị giữ chỗ hết**: tính như không đủ (kho khả dụng = kho thực − giữ chỗ).
- **Uy tín ở biên**: luôn kẹp trong [0, 5]. Bỏ đi ở uy tín 0,3 thì về 0, không âm.
- **Đầu vào sai** (cờ lạ, fixture mâu thuẫn, kho sai schema, khách giữ chỗ vượt kho, hai khách cùng bàn…): thoát mã 2 **trước khi** ghi bất kỳ đầu ra nào.
- **Chạy với `--ticks 0`**: chỉ dựng fixture và ghi snapshot bước 0 cùng dòng kết thúc.
- **Kết xuất lặp lại**: cùng seed, cùng tham số và cùng input thì byte đầu ra giống hệt, kể cả khi người chơi bằng cửa sổ chạy nhanh hay chậm.

## Requirements *(mandatory)*

### Functional Requirements

**Chung (mọi lát)**

- **FR-001**: Game MUST có hai chế độ chơi là buổi sáng (`gather`) và buổi tối (`quan`), dùng **cùng một bộ luật** cho chơi bằng cửa sổ và chạy không giao diện (headless) để chấm tự động.
- **FR-002**: Mô phỏng MUST chạy theo bước cố định 60 bước/giây. Tốc độ hiển thị không được làm đổi kết quả.
- **FR-003**: Mọi số liệu cân bằng (tốc độ, oxy, thời gian nấu, giá…) MUST lấy từ tệp cấu hình hợp đồng của game, không ghi cứng trong luật.
- **FR-004**: Cùng seed, cùng tham số và cùng input MUST cho đầu ra giống hệt từng byte. Ngẫu nhiên chỉ đến từ seed, không đến từ đồng hồ hệ thống.
- **FR-005**: Chế độ headless MUST giữ đúng giao diện dòng lệnh, kiểm tra fixture, trường snapshot, sự kiện, thứ tự sắp xếp theo id và mã thoát (0 bình thường hoặc đạt giới hạn bước, 1 lỗi chạy/ghi, 2 đầu vào sai) của Test Contract §§A–G.
- **FR-006**: Danh sách thực thể trong snapshot MUST sắp theo id tự nhiên (F2 trước F10). Id sinh mới MUST nối tiếp hậu tố lớn nhất đã có và không cấp lại.
- **FR-007**: Nút bấm (`interact`, `catch`) MUST chỉ kích hoạt khi chuyển từ nhả sang nhấn. Hướng di chuyển chéo MUST được chuẩn hóa (không nhanh hơn đi thẳng).

**US1 — Lặn sống sót**

- **FR-010**: Út Sen MUST bơi 4 m/s, tăng/giảm tốc chạm vận tốc mục tiêu trong tối đa 6 bước kể từ khi đổi input, và bị chặn trong x ∈ [0, 100], d ∈ [0, 30]. Vận tốc theo trục bị chặn về 0 ở mép.
- **FR-011**: "Mặt nước" MUST là d ≤ 0,5 tại **cuối** bước. Khi vùng (mặt nước ↔ dưới nước) đổi giữa đầu và cuối bước, hệ thống MUST phát `dive` hoặc `surface`.
- **FR-012**: Oxy tối đa MUST là 1 800. Cuối bước ở dưới nước thì −1. Ở mặt nước thì +6, kẹp trong [0, 1 800]. Khi oxy chuyển từ dương về 0, MUST phát `oxygen_empty` đúng một lần.
- **FR-013**: Bộ đếm ngạt MUST đếm số bước liên tiếp kết thúc ở dưới nước với oxy 0, tính cả bước oxy vừa chạm 0. Đủ 60 thì −1 Máu, phát `choke` và đặt bộ đếm về 0. Ra khỏi điều kiện (nổi lên hoặc có oxy) thì bộ đếm về 0.
- **FR-014**: Máu tối đa MUST là 3 và chỉ ngạt mới gây mất Máu. Máu về 0 thì MUST phát `faint`, rồi `gather_end` lý do `fainted`, và giỏ chuyển đi là rỗng.
- **FR-015**: Giỏ MUST giữ thứ tự nhặt (món mới nhất ở cuối), sức chứa 12, mỗi nguyên liệu chiếm 1 chỗ. Giỏ MUST cho biết còn bao nhiêu chỗ trống để luật hái/bắt dùng chung.

**US2 — Hái, bắt cá, cập bến, xuất kho**

- **FR-020**: `interact` MUST xét cập bến trước: trong bán kính 3 m quanh bến `[2, 0]` thì kết thúc buổi sáng với lý do `docked`.
- **FR-021**: Nếu không cập bến và đang ở mặt nước, `interact` MUST chọn nút **sẵn sàng** gần nhất trong 2 m (bằng nhau thì id nhỏ hơn). Giỏ còn chỗ thì thêm 1 món đúng loại nút, phát `gather` và đặt nút mọc lại sau 1 200 bước. Giỏ đầy thì phát `hold_full` và không đổi gì.
- **FR-022**: Nút đang mọc lại MUST đếm ngược mỗi bước và phát `node_regrown` khi về 0.
- **FR-023**: `catch` MUST chỉ có tác dụng khi ở dưới nước và hồi chiêu bằng 0. Hệ thống chọn đàn cá gần nhất trong 2 m (bằng nhau thì id nhỏ hơn). Giỏ đủ chỗ cho **toàn bộ** sản lượng (cá linh 3, cá lóc 1) thì thêm hết vào giỏ, xóa đàn cá, phát `fish_caught` và đặt hồi chiêu 30 bước. Không đủ chỗ thì phát `hold_full` và không bắt một phần.
- **FR-024**: Phase 1 MUST có sáu đàn cá đứng yên và bốn nút hái theo preset, và fixture được phép thay thế cả hai danh sách.
- **FR-025**: Buổi sáng MUST kết thúc với lý do `docked`, `time` (hết 10 800 bước) hoặc `fainted`. `docked` và `time` chuyển phần còn lại của giỏ, `fainted` chuyển kho rỗng.
- **FR-026**: Kho MUST được ghi **đúng một lần**, một cách nguyên tử, chỉ khi buổi sáng kết thúc, theo đúng schema `{"items":{...}}`: chỉ id nguyên liệu đã biết, số nguyên không âm, bỏ mục bằng 0. Đạt giới hạn bước trước khi kết thúc thì MUST NOT tạo hoặc ghi đè file kho.
- **FR-027**: Buổi tối MUST đọc kho do một tiến trình buổi sáng riêng ghi ra, và snapshot bước 0 có `stock` khớp với nội dung file kho.

**US3 — Khách và đơn hàng**

- **FR-030**: Cơ hội khách đến MUST rơi vào bước 120 và sau đó mỗi 900 bước, cho tới hết ca.
- **FR-031**: Tại mỗi cơ hội có bàn trống, khách MUST chọn đều ngẫu nhiên (theo seed) trong các món **nấu được bằng kho khả dụng**. Không món nào nấu được thì MUST phát `no_dish` và không có khách ngồi.
- **FR-032**: Khi khách gọi món, nguyên liệu của món MUST được giữ chỗ ngay. Kho khả dụng MUST bằng kho thực trừ giữ chỗ, và phần đã giữ chỗ không được hứa cho đơn khác.
- **FR-033**: Kiên nhẫn MUST bắt đầu ở 3 600 và giảm mỗi bước khi khách đang chờ món.
- **FR-034**: Kiên nhẫn về 0 mà chưa được phục vụ thì khách MUST rời đi (`customer_left`), uy tín −0,5 (kẹp [0, 5]), nguyên liệu giữ chỗ chưa nấu được trả lại, và món liên quan (đang nấu, đã chín hay trên tay) bị bỏ. Nguyên liệu đã tiêu khi nấu không hoàn lại.
- **FR-035**: Fixture MUST dựng sẵn được khách ở các trạng thái hợp lệ. Fixture mâu thuẫn (khách giữ chỗ vượt kho, hai khách cùng bàn, bàn không tồn tại, thiếu trường bắt buộc theo trạng thái) MUST bị từ chối với mã 2.

**US4 — Bếp, phục vụ, tiền, uy tín**

- **FR-040**: Mỗi bước MUST xử lý tối đa **một** `interact`. Đối tượng là thứ gần nhất trong 1,5 m (bằng nhau thì bếp trước bàn, rồi theo id), và không chuyển sang đối tượng khác nếu đối tượng đã chọn không dùng được.
- **FR-041**: `interact` tại bếp trống khi tay trống và có đơn đang chờ chưa nấu MUST bắt đầu nấu cho đúng một đơn (`cook_started`) và tiêu nguyên liệu đã giữ chỗ của đơn đó. Sau thời gian nấu (6 s, 4 s, 10 s theo món) bếp chuyển sang chín (`dish_ready`). Món không cháy ở Phase 1.
- **FR-042**: `interact` tại bếp có món chín khi tay trống MUST lấy món lên tay (`dish_picked`). Tay cầm tối đa 1 món.
- **FR-043**: `interact` tại bàn có khách đang chờ đúng món trên tay MUST phục vụ (`served`). Khách ăn 600 bước rồi trả tiền (`paid`).
- **FR-044**: Tiền boa MUST bằng floor(giá × 0,2) nếu kiên nhẫn còn lại lúc phục vụ (sau khi đã giảm của bước đó) ≥ 50%. Nếu không thì bằng 0. Tiền boa dương thì uy tín +0,2 **tại lúc trả tiền**.
- **FR-045**: Tiền MUST tính bằng đơn vị nghìn đồng, số nguyên. Uy tín bắt đầu 3, kẹp [0, 5]. Điểm = tiền kiếm được + 100 × floor(uy tín).
- **FR-046**: Hết ca (10 800 bước), khách đang ăn MUST trả tiền ngay, khách đang chờ rời đi **không** bị trừ uy tín, và `quan_end` là sự kiện cuối.

**US5 — HUD, phản hồi, bằng chứng**

- **FR-050**: Màn hình buổi sáng MUST hiển thị thời gian còn lại, oxy, Máu, giỏ (nội dung và số món/sức chứa).
- **FR-051**: Màn hình buổi tối MUST hiển thị thời gian còn lại, kho khả dụng, đơn của từng khách, kiên nhẫn, trạng thái bếp, món trên tay, tiền, uy tín.
- **FR-052**: Game MUST có phản hồi nhìn thấy được cho: hành động thành công, giỏ đầy, thiếu nguyên liệu, món chín, khách bỏ đi.
- **FR-053**: Hiệu ứng trang trí hoặc sáng tạo thêm MUST NOT đổi đầu ra headless. Chúng phải tắt ở headless hoặc có bằng chứng đầu ra không đổi.
- **FR-054**: Bảng truy vết Phase 1 MUST nối mỗi tiêu chí với cách kiểm, bằng chứng thật từ commit gắn tag, và kết quả đạt/chưa đạt ghi trung thực.

**Quy trình giao nộp (bắt buộc của lab, ảnh hưởng điểm "Làm việc nhóm")**

- **FR-060**: Cả nhóm MUST làm trên một repo chung. Mỗi người trong 5 thành viên MUST có ≥ 3 commit có nội dung bằng tài khoản GitHub của mình (làm cặp thì ghi đồng tác giả).
- **FR-061**: Mỗi thành viên MUST sở hữu rõ phần việc của mình. Chỉ người sở hữu mới sửa phần đó, trừ khi đã báo trước. Điều này để 5 người làm song song mà không đè lên nhau (cách hiện thực ở `plan.md`).
- **FR-062**: Nhánh chính MUST luôn chạy được và qua toàn bộ test công khai tại mọi thời điểm gắn tag. Tag `phase-1` MUST trỏ vào commit trên nhánh chính và được đẩy trước hạn.
- **FR-063**: Câu hỏi, câu trả lời và giả định MUST được ghi tập trung (`docs/clarify.md`). Mỗi người ghi phần dùng AI và phần suy ngẫm cá nhân của mình.

### Key Entities *(include if feature involves data)*

- **Người chơi buổi sáng (Út Sen)**: vị trí [x, d], vận tốc, hướng, oxy, Máu, bộ đếm ngạt, hồi chiêu bắt cá. Thuộc US1, US2 đọc vị trí.
- **Giỏ**: danh sách nguyên liệu theo thứ tự nhặt, sức chứa 12. US1 sở hữu, US2 thêm món.
- **Nút hái**: id, loại (bông điên điển / bông súng), vị trí ở mặt nước, thời gian mọc lại còn lại. Thuộc US2.
- **Đàn cá**: id, loại (cá linh / cá lóc), vị trí dưới nước, sản lượng theo loại. Thuộc US2.
- **Kho (inventory)**: số lượng từng nguyên liệu. Là "hợp đồng" duy nhất giữa buổi sáng và buổi tối.
- **Món (menu)**: id, công thức, thời gian nấu, giá. Dữ liệu cố định.
- **Khách / đơn hàng**: id, bàn, món đã gọi, nguyên liệu giữ chỗ, kiên nhẫn còn lại, trạng thái (đang chờ → đang ăn → đã trả / đã rời). US3 tạo và quản lý chờ/rời, US4 chuyển sang ăn và trả tiền.
- **Bếp**: id, vị trí, trạng thái (trống / đang nấu / chín), món, khách mà món đó thuộc về, thời gian nấu còn lại. Thuộc US4.
- **Bàn**: id, vị trí, khách đang ngồi. US3 xếp khách, US4 phục vụ.
- **Tay người chơi buổi tối**: món đang cầm (tối đa 1) và khách mà món thuộc về. Thuộc US4.
- **Sổ quán**: tiền, tiền kiếm được, uy tín, điểm. US4 ghi khi trả tiền, US3 ghi khi khách bỏ đi.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tại tag `phase-1`, 100% test công khai qua khi chạy từ một bản clone sạch với tối đa 3 lệnh chuẩn bị.
- **SC-002**: Mỗi câu chuyện US1–US4 có ít nhất một bộ kiểm thử riêng chạy độc lập (không cần câu chuyện khác hoàn thành), bao phủ 100% kịch bản chấp nhận của câu chuyện đó.
- **SC-003**: Chạy lại 10 lần cùng seed, tham số và input cho đầu ra giống hệt từng byte cả 10 lần, ở cả hai chế độ.
- **SC-004**: Kịch bản chuyển kho giữa hai tiến trình (cập bến → quán đọc kho) qua được và có bằng chứng **trước phút 25** của Phase 1.
- **SC-005**: Một người chưa xem mã chơi hết một buổi sáng rồi một buổi tối và trả lời đúng "còn bao nhiêu oxy / khách muốn món gì / đang có bao nhiêu tiền" chỉ bằng cách nhìn HUD.
- **SC-006**: Cả 5 thành viên đều có ≥ 3 commit có nội dung, mỗi người có commit trong phần mình sở hữu.
- **SC-007**: Trong Phase 1, mỗi lần gộp vào nhánh chính có tối đa 1 xung đột (conflict) phải xử lý tay, mỗi xung đột xử lý xong dưới 5 phút, và không có xung đột nào trong phần luật của người khác.
- **SC-008**: Nhánh chính không bao giờ ở trạng thái test đỏ quá 10 phút liên tục trong giờ lab.
- **SC-009**: 100% tiêu chí trong bảng truy vết Phase 1 có bằng chứng tái tạo được từ đúng commit gắn tag.

## Assumptions

- Phạm vi spec này là **Phase 1** (PRD-0, Test Contract v1.0). Phase 2–4 chưa có PRD và sẽ là feature riêng (`002-…`), nhưng phần chia lát và sở hữu được thiết kế để mở rộng được.
- Nhóm **giữ khung kỹ thuật (starter)** do giảng viên cấp (đã có giao diện dòng lệnh, kiểm fixture, vòng bước, ngẫu nhiên theo seed, ghi kho). Công nghệ chốt ở `plan.md`.
- Phần mở rộng (nhóm 5 người phải có ít nhất 1 trong cả lab) **chưa nằm trong Phase 1**. Nhóm chọn ở phase sau khi lõi đã đúng.
- Bàn duy nhất (`T1`) đang có khách lúc tới lượt khách mới: không có khách mới và không phát `no_dish`. PO cần xác nhận với Test Contract §F và ghi vào `docs/clarify.md`.
- `catch` khi giỏ không đủ chỗ: phát `hold_full`, **không** đặt hồi chiêu. PO cần xác nhận.
- Bếp nấu cho đơn **đang chờ, chưa nấu, có id nhỏ nhất** khi có nhiều đơn. Phase 1 chỉ có 1 bàn nên hiếm xảy ra. PO cần xác nhận.
- Cập bến không đòi hỏi phải ở mặt nước, chỉ cần trong bán kính 3 m quanh bến (đúng như khung starter).
- Tên sự kiện và trường dữ liệu đi kèm theo Test Contract §E. Danh sách đang dùng ở `contracts/events.md` lấy từ starter và **phải được đối chiếu** trước khi chốt.
- Hạn Phase 1 là 60 phút kể từ mốc 0:00 của lab (`phase-1` trước 1:00), theo README.
- Mọi thành viên dùng Windows hoặc macOS/Linux. Hướng dẫn chạy cần có cả hai biến thể lệnh.
