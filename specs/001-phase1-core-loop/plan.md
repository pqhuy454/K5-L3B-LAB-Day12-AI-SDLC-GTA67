# Implementation Plan: Phase 1 — Vòng lõi Lặn & Hái → Kho → Mở Quán

**Branch**: `001-phase1-core-loop` | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-phase1-core-loop/spec.md`

## Summary

Hiện thực vòng lõi Phase 1 (lặn sống sót, hái/bắt cá, xuất kho, khách/giữ chỗ, bếp/phục vụ/tiền, HUD) trên **starter Python** sẵn có, sao cho **5 người code song song mà gần như không conflict khi merge**. Cách làm:

1. **Tách mỗi lát thành một module riêng** (`chonoi/sim/gather_survival.py`, `gather_harvest.py`, `quan_orders.py`, `quan_kitchen.py`). Mỗi module chỉ có một chủ.
2. `gather.py` và `quan.py` chỉ còn là **bộ điều phối mỏng** (orchestrator). Chúng gọi các hàm hook theo đúng thứ tự trong Test Contract §F. Integrator viết **một lần duy nhất** trong "commit khung" đầu Phase 1, sau đó gần như không ai sửa.
3. **Hợp đồng hook + quyền ghi theo từng trường dữ liệu** được chốt trong [`contracts/sim-hooks.md`](contracts/sim-hooks.md) trước khi chia việc.
4. **Test, bằng chứng và tài liệu tách theo người** (file riêng hoặc mục dựng sẵn), cộng với quy trình git nhánh ngắn, rebase thường xuyên, không squash và không tự format file của người khác.

## Technical Context

**Language/Version**: Python 3.10+ (chỉ thư viện chuẩn). Trên máy Windows dùng `python`, trên macOS/Linux dùng `python3`. CI chạy 3.12.

**Primary Dependencies**: Không có (stdlib). Cửa sổ chơi dùng `http.server` và một trang HTML tĩnh (`chonoi/web/index.html`).

**Storage**: File JSON (kho `{"items":{...}}`, fixture, inputs) và JSONL (log headless), ghi nguyên tử bằng `chonoi/inventory.py`.

**Testing**: `unittest`. Test hộp đen chạy qua `headless_cmd` (`tests/test_smoke_p1.py`) + test riêng từng lát (file riêng mỗi người).

**Target Platform**: CLI headless trên Linux (chấm tự động) + trình duyệt cho chơi thử. Thành viên dev trên Windows/macOS.

**Project Type**: CLI game simulation + web client tĩnh.

**Performance Goals**: 10 800 bước/buổi chạy headless dưới ~2 s; cửa sổ chơi giữ 60 bước/s.

**Constraints**: Tất định từng byte (FR-004). Không đồng hồ hệ thống và không `random` toàn cục. Mã thoát 0/1/2. Không ghi cứng số liệu. Hạn 60 phút.

**Scale/Scope**: 5 người, 4 lát luật + 1 lát UI/QA, khoảng 600–900 dòng mã mới cho Phase 1.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Dự án chưa có `.specify/memory/constitution.md`. Các "quy tắc vàng" trong `AGENTS.md` và `docs/STARTER.md` được dùng làm cổng kiểm:

| Cổng | Nguồn | Kế hoạch có đạt? |
|---|---|---|
| G1. Số liệu chỉ đọc từ `game.contract.json` | AGENTS.md | ✅ Mọi hook đọc `sim.t` / `sim.menu`, không có hằng số luật trong module lát |
| G2. Ngẫu nhiên chỉ qua `Streams`, không đồng hồ hệ thống | AGENTS.md | ✅ Lát 3 dùng luồng riêng `customer_order` (xem research R10) |
| G3. Sắp bằng `sort_by_id`, cấp id bằng `IdAllocator` | AGENTS.md | ✅ `pick.nearest` dùng `id_key` để phá hòa; khách mới dùng `sim.ids.new("C")` |
| G4. Không sửa `docs/contracts/`, `game.contract.json`, schema kho khi chưa báo cả nhóm | AGENTS.md | ✅ Hai file đó do Integrator giữ (bảng sở hữu bên dưới) |
| G5. Không làm hỏng nhánh chính: chạy test trước khi đẩy | AGENTS.md | ✅ Vòng làm việc ở quickstart §3 bắt buộc chạy test trước push |
| G6. Không sửa test cho xanh khi luật sai | AGENTS.md | ✅ Test công khai do QA giữ, chỉ đọc với người khác |
| G7. Khung giảng viên hạn chế sửa | AGENTS.md | ⚠️ Commit khung **có** sửa `scenario.py`, `gather.py`, `quan.py` (thêm lời gọi hook). Lý do ở Complexity Tracking |

Kiểm lại sau thiết kế: vẫn đạt. G7 có lý do được ghi nhận.

## Project Structure

### Documentation (this feature)

```text
specs/001-phase1-core-loop/
├── spec.md              # CÁI GÌ / VÌ SAO (5 user story ↔ 5 người)
├── checklists/requirements.md
├── plan.md              # File này: CÁCH LÀM + chiến lược tránh conflict
├── research.md          # Quyết định + lý do + phương án bị loại
├── data-model.md        # Thực thể, trường, ai được ghi trường nào, chuyển trạng thái
├── contracts/
│   ├── sim-hooks.md     # Chữ ký hàm từng lát + ma trận quyền ghi trường
│   └── events.md        # Tên sự kiện, payload, lát phát
├── quickstart.md        # Lệnh kiểm chứng + vòng git hằng ngày + xử lý conflict
└── tasks.md             # (phase tasks, chưa tạo)
```

### Source Code (repository root)

Cột **Chủ** là người duy nhất được sửa nội dung file sau commit khung. Người khác muốn đổi thì nhắn chủ (hoặc làm cặp với `Co-authored-by:`).

```text
chonoi/
├── headless.py  inputs.py  contract.py  rng.py  ids.py      # KHUNG GV — Chủ: Phạm Quốc Huy (Integrator). Không sửa.
├── jsonl.py  inventory.py  runner.py  errors.py  __init__.py  # KHUNG GV — như trên
├── scenario.py          # Chủ: Integrator. Commit khung thêm 2 lời gọi validate của lát 3/4, sau đó đóng băng
├── live.py              # Chủ: Trịnh Gia Huy (Lát 5)
├── web/index.html       # Chủ: Trịnh Gia Huy (Lát 5) — HUD, phản hồi, đồ họa
└── sim/
    ├── __init__.py  ramp.py   # KHUNG GV
    ├── pick.py           # MỚI — chọn đối tượng gần nhất. Integrator viết đầy đủ trong commit khung
    ├── hold.py           # MỚI — giỏ: free_slots/push_all/clear. Chủ: Trần Duy Thành (Lát 1), viết đầy đủ trong commit khung
    ├── gather.py         # BỘ ĐIỀU PHỐI sáng. Chủ: Integrator. Chỉ chứa thứ tự bước + snapshot + _move/_finish
    ├── gather_survival.py# MỚI — Chủ: Trần Duy Thành (Lát 1): dive/surface, oxy, ngạt, ngất
    ├── gather_harvest.py # MỚI — Chủ: Đoàn Anh Hùng (Lát 2): hái nút, bắt cá
    ├── quan.py           # BỘ ĐIỀU PHỐI tối. Chủ: Integrator. Chỉ chứa thứ tự bước + snapshot + _move
    ├── ledger.py         # MỚI — tiền/uy tín có kẹp. Chủ: Phạm Quốc Huy (Lát 4), viết đầy đủ trong commit khung
    ├── quan_orders.py    # MỚI — Chủ: Đặng Đức Minh (Lát 3): khách, chọn món, giữ chỗ, kiên nhẫn, bỏ đi, validate fixture khách
    └── quan_kitchen.py   # MỚI — Chủ: Phạm Quốc Huy (Lát 4): bếp, bưng, phục vụ, ăn, trả tiền, đóng ca

tests/
├── helpers.py  test_smoke_p1.py  test_python_starter_units.py  test_live.py   # Chủ: Trịnh Gia Huy (QA). Người khác CHỈ ĐỌC
├── test_gather_survival.py   # MỚI — Lát 1
├── test_gather_harvest.py    # MỚI — Lát 2
├── test_quan_orders.py       # MỚI — Lát 3
├── test_quan_kitchen.py      # MỚI — Lát 4
└── test_integration_p1.py    # MỚI — Lát 5 / QA (hai tiến trình, tất định, vòng đầy đủ)

game.contract.json            # Chủ: Integrator. Phase 1 KHÔNG đổi tuning (dùng preset)
docs/contracts/               # Chủ: Integrator
.gitattributes                # MỚI (commit khung) — chuẩn hóa xuống dòng LF
```

**Structure Decision**: Giữ nguyên starter và layout một project. Chỉ **thêm file mới** cho từng lát. Theo cách git hoạt động, **file mới do một người tạo thì không bao giờ conflict**. Conflict chỉ có thể xảy ra ở ba file điều phối (`gather.py`, `quan.py`, `scenario.py`), nên ba file này được viết xong trong **một commit khung duy nhất** trước khi tách việc, rồi đóng băng.

## Chiến lược tránh conflict khi merge

### 1. Vì sao không làm thẳng trên starter

Trong starter, **Lát 1 và Lát 2 cùng sửa một hàm** `GatherSim.step()` ([chonoi/sim/gather.py](../../chonoi/sim/gather.py)), **Lát 3 và Lát 4 cùng sửa một hàm** `QuanSim.step()` ([chonoi/sim/quan.py](../../chonoi/sim/quan.py)). Các `TODO(nhóm)` cách nhau chỉ 1–3 dòng, nên git gần như chắc chắn báo conflict. Tệ hơn, hai người có thể cùng thêm trường `self.xxx` vào `__init__` với nghĩa khác nhau.

### 2. Commit khung (T000) — Integrator làm trong 10 phút đầu, trước khi ai viết luật

Một commit duy nhất, đẩy thẳng lên `main`, mọi người `git pull` ngay sau đó:

1. Tạo các module lát **dạng stub** (hàm có chữ ký đúng như [`contracts/sim-hooks.md`](contracts/sim-hooks.md), thân là `pass` hoặc trả giá trị rỗng) để import không lỗi và test hiện có vẫn xanh.
2. Viết lại `GatherSim.step()` và `QuanSim.step()` thành **chuỗi lời gọi hook** theo thứ tự Test Contract §F (xem sim-hooks.md §Thứ tự bước). Mọi trường trạng thái khai báo sẵn trong `__init__` (kể cả trường Lát 3/4 cần như `self.step_no`, `self.hand`).
3. Viết **đầy đủ** các helper nhỏ dùng chung: `pick.nearest`, `hold.*`, `ledger.*`. Đây là chỗ hai lát cùng dùng, nên phải có thật từ đầu để không ai phải chờ.
4. Thêm 2 dòng cuối `_validate_quan` trong `scenario.py`: `quan_orders.validate_scenario(b, tuning)` và `quan_kitchen.validate_scenario(b, tuning)`.
5. `snapshot()` của quán lọc bỏ trường bắt đầu bằng `_` khỏi khách (trường nội bộ không lộ ra JSONL, xem data-model).
6. Tạo 5 file test rỗng (một `TestCase` với `pass`) cho 5 người.
7. Dựng sẵn **mục theo người** trong các tài liệu dùng chung (§4) và thêm `.gitattributes`.
8. Thêm bảng sở hữu file (bảng ở trên, rút gọn) vào `AGENTS.md`, để agent AI của mọi người đọc và không sửa lan sang file người khác.
9. Chạy `PYTHONPATH=tests:. python -m unittest discover -s tests -v`, phải xanh rồi mới push.

> Trong 10 phút này, 4 người còn lại **không đụng file có sẵn**. Họ đọc spec, viết test cho lát mình trong một **file mới** (sẽ đổi tên đúng sau khi pull khung), và PO hỏi 3 giả định trong spec với giảng viên.

### 3. Quy tắc code để không giẫm chân nhau

| # | Quy tắc | Lý do |
|---|---|---|
| C1 | Chỉ sửa file mình là **Chủ**. Cần thêm lời gọi hook hoặc trường mới ở bộ điều phối thì nhắn Integrator, không tự sửa | Bộ điều phối là điểm nóng duy nhất |
| C2 | Module lát **chỉ nhận `sim` làm tham số** (hàm thuần thủ tục), không import `gather.py`/`quan.py` | Tránh vòng import, test được riêng |
| C3 | Hướng phụ thuộc một chiều: `quan_kitchen → quan_orders → ledger`, `gather_harvest → hold, pick`. **Không** import ngược | Hai người không phải sửa file nhau để "nối dây" |
| C4 | Chỉ ghi các trường mình có **quyền ghi** theo ma trận ở sim-hooks.md. Cần đổi trường của lát khác thì gọi hàm API của lát đó (ví dụ Lát 4 gọi `quan_orders.consume_reserved`) | Tránh lỗi logic không hiện ra thành conflict git |
| C5 | Trường nội bộ mới chỉ được thêm vào **dict/thực thể của mình** và đặt tên bắt đầu bằng `_` (ví dụ `c["_cook_started"]`). Không thêm `self.xxx` vào sim ngoài commit khung | Không ai chèn dòng vào `__init__` chung |
| C6 | Tên sự kiện là chuỗi đúng y [`contracts/events.md`](contracts/events.md). Đổi tên thì Integrator sửa hợp đồng trước | Test ẩn so tên |
| C7 | Không bật "format on save", không chạy black/isort/autopep8 lên **cả repo** hoặc file người khác. Import chỉ thêm vào cuối khối import của file mình | Format lại cả file = conflict toàn file |
| C8 | Không đổi tên, di chuyển hay xóa file có sẵn trong Phase 1 (kể cả asset) nếu không báo trước | Rename + sửa song song = conflict khó gỡ |
| C9 | Không sửa `game.contract.json`. Cần số liệu mới thì nhờ Integrator | Mọi test đọc file này |
| C10 | Khi nhờ agent AI: luôn nói rõ "chỉ được sửa `<file của tôi>` và `tests/test_<lát>.py`". Đọc lại diff và kiểm `git diff --stat` trước khi commit, không có file lạ thì mới commit | AI hay "tiện tay" refactor bộ điều phối hoặc format cả file |
| C11 | Commit nhỏ, một ý, chạy test trước. Không commit file sinh ra (`*.jsonl`, `__pycache__`, file kho tạm) | `.gitignore` đã chặn phần lớn |

### 4. Tài liệu dùng chung — ai ghi, ghi ở đâu

| File | Chủ | Cách ghi không conflict |
|---|---|---|
| `docs/clarify.md` | Thành (PO) | Chỉ PO ghi. Người khác nhắn câu hỏi qua Zalo |
| `docs/ai-usage-log.md` | Mỗi người | Commit khung dựng 5 mục `## <handle>`, mỗi người **chỉ chèn dòng trong mục mình** |
| `docs/standup.md` | Hùng (Scrum) | Scrum ghi hộ cả nhóm sau mỗi standup (một commit) |
| `docs/verification/phase-1.md` | Gia Huy (QA) | Commit khung dựng 5 bảng con `### US1…US5`. Chủ lát điền dòng trong bảng của mình, QA điền phần "Đánh giá ngắn" |
| `docs/proof/phase-1/<handle>/` | Mỗi người | Thư mục riêng, file mới → không conflict |
| `docs/members/<handle>.md` | Mỗi người | File riêng |
| `AGENTS.md` | Integrator | Commit khung dựng mục "Skills của nhóm" có 5 dòng `- <handle>: …`, mỗi người chỉ sửa dòng của mình. Skill để ở `.agents/skills/<handle>-<tên>/` |
| `README.md`, `CHANGELOG.md` | Hùng (Release) | Chỉ sửa lúc chuẩn bị tag |
| `TEAM.md` | Thành (PO) | — |
| `CREDITS.md` | Gia Huy (UI) | Người thêm asset nhắn UI để ghi nguồn |
| `game.contract.json`, `docs/contracts/` | Phạm Quốc Huy (Integrator) | — |

Mẹo git: hai người chèn dòng **sát nhau** (liền dòng) vẫn bị conflict, còn chèn ở hai mục cách nhau ít nhất một dòng không đổi thì git tự gộp được. Vì vậy mỗi mục dựng sẵn đều có tiêu đề và dòng trống ngăn cách.

### 5. Quy trình Git

- **Nhánh tích hợp duy nhất là `main`** (tag phải nằm trên `main`). Nhánh `intergration` hiện đang **đi trước `main` 3 commit asset**: Integrator gộp nó vào `main` một lần trước commit khung, sau đó thôi dùng. Nhánh tích hợp sống lâu chính là nguồn conflict lớn.
- Nhánh cá nhân ngắn: `<handle>/p1-<việc>` (ví dụ `thanh289/p1-oxygen`), sống **≤ 20 phút**.
- Trước khi push: `git fetch origin && git rebase origin/main`, sau đó chạy test, rồi push. Nếu rebase báo conflict ở file không phải của mình thì **dừng lại và gọi chủ file** (quickstart §4).
- Gộp vào `main` bằng PR, chọn **"Rebase and merge" hoặc "Create a merge commit", KHÔNG "Squash"**. Squash gộp nhiều commit thành một và làm hụt chỉ tiêu ≥ 3 commit/người (FR-060). Không dùng PR thì `git pull --rebase` rồi push thẳng, cũng được.
- Thứ tự gộp khi có phụ thuộc: hàm API của Lát 3 (`available_stock`, `consume_reserved`, `pending_order`) gộp **trước** phần dùng chúng của Lát 4. Trong lúc chờ, Lát 4 test bằng khách dựng sẵn trong fixture.
- Không `push --force` lên `main`. Trên nhánh của mình thì dùng `--force-with-lease`.
- Integrator là người duy nhất gắn tag, chỉ khi QA báo `main` xanh.

### 6. Lịch Phase 1 gắn với gộp code

| Phút | Việc | Ai |
|---|---|---|
| 0–10 | Gộp `intergration`→`main`; commit khung T000; PO hỏi 3 giả định | Integrator, PO |
| 0–10 | Viết test (file mới) cho lát mình | Còn lại |
| 10 | Mọi người `git pull` khung, tạo nhánh cá nhân | Tất cả |
| 10–45 | Code song song, gộp vào `main` mỗi ≤ 15–20 phút | Tất cả |
| 20 | Standup 2 phút: ai chậm thì người dự phòng nhận việc | Scrum |
| ≤ 25 | Demo chuyển kho hai tiến trình (SC-004) | Lát 2 + QA |
| 45–55 | Đóng băng tính năng, QA chạy toàn bộ quickstart, điền verification/proof | QA + chủ lát |
| 55–60 | Tag `phase-1` trên `main`, push tag | Integrator |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| G7: sửa khung GV (`gather.py`, `quan.py`, `scenario.py`) | Biến `step()` thành bộ điều phối gọi hook, để 4 người không cùng sửa một hàm | "Mỗi người sửa thẳng `step()`": TODO của hai lát cách nhau 1–3 dòng, conflict gần như chắc chắn và tốn thời gian gỡ trong lab 60 phút |
| Thêm 7 module mới | Mỗi lát một file với một chủ, file mới không thể conflict | "Một file / một mode": hai người một file, conflict thường xuyên |
