# Quickstart — kiểm chứng Phase 1 và làm việc với git

> Lệnh viết cho **bash (macOS/Linux/Git Bash)**. Trên **PowerShell** đổi `python3` → `python` và `PYTHONPATH=tests:. cmd` → `$env:PYTHONPATH="tests;."; cmd`.

## 1. Chuẩn bị (clone sạch, ≤ 3 lệnh)

```bash
git clone https://github.com/pqhuy454/K5-L3B-LAB-Day12-AI-SDLC-GTA67 && cd K5-L3B-LAB-Day12-AI-SDLC-GTA67
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather        # chơi thử: WASD/mũi tên, E, Space, R
```

## 2. Kịch bản kiểm chứng (trỏ tới spec)

| # | Kiểm | Lệnh | Kết quả mong đợi | Spec |
|---|---|---|---|---|
| Q1 | Test từng lát | `PYTHONPATH=tests:. python3 -m unittest tests.test_gather_survival -v` (đổi tên module theo lát) | xanh | SC-002 |
| Q2 | Toàn bộ test | `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` | xanh | SC-001 |
| Q3 | Chuyển kho hai tiến trình | xem khối dưới | snapshot quán bước 0 có `"stock":{"bong_sung":2,"ca_loc":1}` | US2/AC7, SC-004 |
| Q4 | Tất định | chạy 2 lần cùng seed/input rồi `cmp a.jsonl b.jsonl` | không khác byte nào | FR-004, SC-003 |
| Q5 | Đầu vào sai | `--ticks -1` hoặc fixture sai | mã thoát 2, **không** có file `--out` | FR-005 |
| Q6 | Ngạt và ngất | fixture `{"gather":{"player":{"pos":[50,10],"oxygen_ticks":1}}}`, `--ticks 200` | `choke` ở tick 60, 120, 180; cùng tick 180 có thêm `faint` + `gather_end` lý do `fainted`, kho `{}` | US1/AC3-4 |
| Q7 | Vòng quán đầy đủ | fixture khách dựng sẵn + inputs nấu → lấy → phục vụ | `cook_started → dish_ready → dish_picked → served → paid`, tiền đúng giá + tip | US4 |
| Q8 | HUD | `python3 -m chonoi.live --mode quan` | đủ mục FR-051 | US5 |

Q3: smoke test hai tiến trình (bắt buộc Phase 1):

```bash
mkdir -p /tmp/p1 && cd /tmp/p1
echo '{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' > dock.json
echo '{"frames":[{"tick":0,"interact":true}]}' > dock-inputs.json
R=<đường-dẫn-repo>
(cd $R && python3 -m chonoi.headless --mode gather --seed 42 --scenario /tmp/p1/dock.json --inputs /tmp/p1/dock-inputs.json --ticks 1 --out /tmp/p1/gather.jsonl --inventory-out /tmp/p1/catch.json)
(cd $R && python3 -m chonoi.headless --mode quan --seed 42 --inventory /tmp/p1/catch.json --ticks 0 --out /tmp/p1/quan.jsonl)
cat catch.json; head -1 quan.jsonl
```

Lưu đầu ra thật vào `docs/proof/phase-1/<handle>/` và ghi đường dẫn vào bảng US tương ứng trong `docs/verification/phase-1.md`.

## 3. Vòng làm việc git của mỗi người (lặp mỗi ≤ 15–20 phút)

```bash
git switch main && git pull --rebase                    # 1. lấy main mới nhất
git switch -c <handle>/p1-<việc>                        # 2. nhánh ngắn
# ... chỉ sửa file mình là Chủ (plan.md bảng sở hữu) ...
git diff --stat                                         # 3. KHÔNG có file của người khác? (nhất là sau khi dùng AI)
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v   # 4. phải xanh
git add <file của mình> && git commit -m "L1: oxy giảm dưới nước (FR-012)"
git fetch origin && git rebase origin/main              # 5. cập nhật trước khi đẩy
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v   # 6. xanh lại sau rebase
git push -u origin HEAD                                 # 7. mở PR → Rebase and merge (KHÔNG squash)
```

Quy ước commit: `<Lát>: <việc> (<FR/AC>)`. Ví dụ `L3: giữ chỗ nguyên liệu khi khách gọi món (FR-032)`. Làm cặp thì thêm dòng `Co-authored-by: Tên <email>`.

## 4. Khi gặp conflict

1. `git status` để xem file nào conflict.
2. **File của mình**: sửa, `git add`, `git rebase --continue`.
3. **File của người khác hoặc bộ điều phối** (`gather.py`, `quan.py`, `scenario.py`, `game.contract.json`, docs chung): **không** chọn bừa "ours/theirs". `git rebase --abort`, nhắn chủ file (Zalo), cùng sửa hoặc để chủ sửa. Đó thường là dấu hiệu ai đó đã vi phạm quy tắc C1.
4. Sau khi gỡ: chạy lại toàn bộ test trước khi push.
5. Ghi một dòng vào `docs/retro.md` (Scrum ghi): conflict ở đâu, vì sao, để retro.

## 5. Checklist trước khi Integrator gắn tag `phase-1`

- [ ] `main` có mọi nhánh lát, toàn bộ test xanh trên bản clone sạch (Q2)
- [ ] Q3, Q4 có bằng chứng trong `docs/proof/phase-1/`
- [ ] `docs/verification/phase-1.md` đủ 5 bảng US, kết quả ghi trung thực
- [ ] `TEAM.md`, `game.contract.json` (`team_size: 5`), `docs/clarify.md`, `docs/ai-usage-log.md` cập nhật
- [ ] Mỗi người ≥ 1 commit có nội dung trong phase này (mục tiêu ≥ 3 cả lab)
- [ ] `git tag phase-1 && git push origin phase-1` từ `main`
