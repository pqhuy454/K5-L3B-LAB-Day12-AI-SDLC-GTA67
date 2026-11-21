# Research — Phase 1

## R1. Công nghệ
- **Decision**: Giữ starter Python 3 (stdlib) trong `chonoi/`.
- **Rationale**: CLI, kiểm fixture, mã thoát, vòng bước, RNG, ghi kho nguyên tử và cửa sổ chơi đã có và đã qua smoke test. Trong 60 phút, thời gian nên dồn cho luật.
- **Alternatives considered**: Godot/Pygame/JS. Bị loại vì phải viết lại headless + Test Contract từ đầu.

## R2. Chia mã theo lát để tránh conflict
- **Decision**: Mỗi lát một module riêng, có một chủ. `gather.py`/`quan.py` chỉ là bộ điều phối gọi hook theo thứ tự §F.
- **Rationale**: Git chỉ conflict khi hai nhánh sửa cùng/sát dòng của **cùng file**. File mới của một người không bao giờ conflict. Thứ tự bước (thứ dễ sai và hay đổi khi đối chiếu Test Contract) gom về **một** chỗ có một chủ.
- **Alternatives considered**:
  - Mọi người sửa thẳng `step()`: TODO của hai lát cách nhau 1–3 dòng, gần như chắc chắn conflict.
  - Mixin class (`class GatherSim(SurvivalMixin, HarvestMixin)`): khả thi, nhưng chung namespace `self` nên dễ trùng tên method/thuộc tính mà git không báo. Hàm `f(sim, events)` thì tường minh hơn và test riêng dễ hơn.
  - Mỗi lát một nhánh dài rồi gộp cuối giờ: conflict dồn cục ở phút 50, đúng lúc nguy hiểm nhất.

## R3. Commit khung trước khi tách việc
- **Decision**: Integrator làm một commit T000 trong 10 phút đầu: stub mọi module, nối dây bộ điều phối, helper dùng chung đầy đủ, file test rỗng, mục tài liệu theo người, `.gitattributes`.
- **Rationale**: Mọi dòng mà nhiều người cùng cần chạm đều được viết **một lần, bởi một người, trước khi** có nhánh song song.
- **Alternatives considered**: Mỗi người tự thêm lời gọi hook khi cần. Bị loại vì bộ điều phối sẽ bị 4 người sửa cùng lúc.

## R4. Quyền ghi theo trường + hướng import một chiều
- **Decision**: Ma trận quyền ghi trong `contracts/sim-hooks.md`. Lát 4 muốn đổi trạng thái của Lát 3 thì gọi API của Lát 3. Import một chiều `quan_kitchen → quan_orders → ledger`. Bộ điều phối nối chiều ngược (`discard_dish_for`).
- **Rationale**: Tránh "conflict logic" (git gộp sạch nhưng hai người cùng trừ kho hoặc cùng cộng uy tín) và tránh vòng import.
- **Alternatives considered**: Event bus nội bộ. Bị loại vì quá nặng cho 60 phút và khó giữ thứ tự tất định.

## R5. Trường nội bộ đặt tiền tố `_`, snapshot lọc bỏ
- **Decision**: Lát thêm trạng thái riêng vào dict của mình với khóa `_xxx`. `QuanSim.snapshot()` lọc khóa `_` của khách.
- **Rationale**: Starter đang dump **nguyên** dict khách ra snapshot. Thêm trường tùy ý sẽ làm đổi JSONL và có thể lệch so với Test Contract.
- **Alternatives considered**: Bảng phụ `sim._orders_state`. Bị loại vì phải thêm `self.xxx` vào `__init__` chung.

## R6. Quy trình git
- **Decision**: Trunk-based trên `main`. Nhánh cá nhân `<handle>/p1-<việc>` sống ≤ 20 phút. `git rebase origin/main` trước push. PR gộp bằng **rebase-merge hoặc merge commit, không squash**. Chỉ Integrator gắn tag.
- **Rationale**: Nhánh càng ngắn thì conflict càng nhỏ. Squash làm mất commit riêng của từng người (ảnh hưởng chỉ tiêu ≥ 3 commit/người). Tag phải nằm trên `main`.
- **Alternatives considered**: Nhánh `intergration` sống lâu rồi gộp vào `main` cuối phase. Bị loại vì dồn conflict về cuối, và tag phải trên `main`. Nhánh `intergration` hiện có (đi trước `main` 3 commit asset) được gộp một lần rồi thôi dùng.

## R7. Xuống dòng và định dạng
- **Decision**: Thêm `.gitattributes` với `* text=auto eol=lf` và `*.png binary` (cùng các định dạng ảnh/âm thanh khác). Không dùng auto-formatter toàn repo.
- **Rationale**: Thành viên dùng Windows. Nếu CRLF/LF lẫn lộn, cả file bị coi là "đã sửa", conflict toàn file. Formatter chạy trên file người khác cũng gây hiệu ứng tương tự.
- **Alternatives considered**: Mỗi người tự `core.autocrlf`. Bị loại vì không đảm bảo đồng nhất.

## R8. Tài liệu dùng chung
- **Decision**: File cá nhân (`docs/members/<handle>.md`, `docs/proof/phase-1/<handle>/`). File chung thì dựng sẵn mục theo người (ai-usage-log, verification, AGENTS skills) hoặc chỉ một chủ ghi (clarify, standup, README, CHANGELOG).
- **Rationale**: Thêm dòng cuối bảng là kiểu conflict phổ biến nhất trong lab nhóm.

## R9. Agent AI và phạm vi sửa
- **Decision**: Bảng sở hữu file đưa vào `AGENTS.md`. Prompt cho agent luôn kèm "chỉ sửa <file của tôi>". Kiểm `git diff --stat` trước commit.
- **Rationale**: Agent hay sửa lan (refactor bộ điều phối, format lại import, sửa test cho xanh), tạo conflict và vi phạm G6.

## R10. Luồng ngẫu nhiên
- **Decision**: Lát 3 dùng `sim.rng.get("customer_order")` để chọn món. Danh sách món nấu được được sắp theo id món trước khi chọn. Phase sau mỗi tính năng ngẫu nhiên mới dùng một tên luồng riêng, đăng ký ở đây.
- **Rationale**: `Streams` seed theo (seed, tên), nên thêm tính năng không làm lệch chuỗi của tính năng khác. Đây là điều kiện để giữ tất định từng byte.

## R11. Số thực của uy tín
- **Decision**: `ledger.add_reputation` làm tròn 6 chữ số sau khi cộng, rồi mới kẹp.
- **Rationale**: Cộng 0,2 nhiều lần có thể ra 4.999999…, `floor` ra 4 thay vì 5 và làm sai điểm.

## R12. Điểm còn phải đối chiếu Test Contract (PO ghi kết quả vào `docs/clarify.md`)
1. Tên sự kiện khách đến và payload các sự kiện (`contracts/events.md`, dòng ⚠️).
2. Trường snapshot của khách, bếp, tay (`data-model.md`, dòng ⚠️).
3. Thứ tự các bước trong một tick của quán (§F). Chỉ ảnh hưởng `quan.py` (Integrator).
4. Ba giả định trong spec: bàn đầy lúc tới lượt khách, hồi chiêu khi bắt thất bại, chọn đơn để nấu.
5. Mốc "tick 120" của khách đầu tiên tính theo bước đã chạy hay theo thời gian đã trôi của ca (khác nhau khi fixture đặt `time_left_ticks`).
