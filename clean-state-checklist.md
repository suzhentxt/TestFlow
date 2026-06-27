# Danh sách Kiểm tra Trạng thái Sạch

Checklist này dùng cho TestFlow trước khi kết thúc một phiên agent.

## Checklist Chung

- [ ] Đã chạy `pwd` và đang ở root repo.
- [ ] Đã đọc `README.md`, `claude-progress.md`, và `feature_list.json`.
- [ ] Đã chọn đúng một feature active hoặc ghi rõ không làm feature product.
- [ ] Baseline phù hợp môi trường đã chạy:
  - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1`
  - Bash: `./init.sh`
- [ ] Kết quả xác minh được ghi lại trong `claude-progress.md` hoặc `feature_list.json`.
- [ ] `feature_list.json` phản ánh đúng trạng thái: chỉ feature có bằng chứng mới được `passing`.
- [ ] Không có bước làm dở nào bị bỏ lại mà không ghi trong `session-handoff.md`.
- [ ] Rủi ro, blocker, hoặc phần chưa xác minh được ghi rõ.
- [ ] Repo đủ rõ để phiên sau bắt đầu bằng baseline chuẩn.
- [ ] Nếu trạng thái an toàn, đã commit thay đổi liên quan.

## Checklist Riêng Cho TestFlow

- [ ] Nếu chỉnh orchestration, planner, runner, coverage, verifier, hoặc report, có test đơn vị cho hành vi đó.
- [ ] Nếu sinh hoặc repair tests, production source không bị sửa ngoài phạm vi feature.
- [ ] Nếu parser đọc pytest/coverage output, có fixture cho cả case pass và fail.
- [ ] Nếu feature dùng LLM, có seam/interface để test deterministic mà không gọi network.
- [ ] Nếu nâng baseline từ docs-only sang implementation, `init.ps1` và `init.sh` cùng được cập nhật.
- [ ] Python/pip/pytest/TestFlow commands chạy qua `.venv`, không chạy qua môi trường global ngoài bước bootstrap.

## Trạng thái Phiên 2026-06-27

| Hạng mục | Trạng thái | Bằng chứng/Ghi chú |
| --- | --- | --- |
| Root repo | Đã xác nhận | `pwd` -> `D:\TestFlow` |
| Baseline Bash | Bị chặn bởi môi trường | Bash gọi WSL nhưng chưa có distro |
| Baseline PowerShell | Đã chạy ngoài sandbox | `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1` exit 0; dùng `.venv`; `tests/test_state.py` pass |
| Feature đang xử lý | Một phần đã xác minh | Runtime state smoke test pass; product feature/CLI vẫn chưa hoàn thành |
| Feature product kế tiếp | `tf-001` | Create installable Python CLI skeleton |
| Commit | Chưa tạo được | Sandbox không cho ghi `.git/index.lock`; escalation cho `git add` bị từ chối |
