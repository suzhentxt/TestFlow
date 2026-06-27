# Nhật ký Tiến độ

## Trạng thái Đã xác minh Hiện tại

- Thư mục gốc kho lưu trữ: `D:\TestFlow`
- Product spec hiện tại: `README.md`
- Đường dẫn khởi động/xác minh chuẩn trên Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1`
- Đường dẫn khởi động/xác minh chuẩn trên Bash: `./init.sh`
- Phạm vi baseline hiện tại: docs/process validation. Repo chưa có `pyproject.toml`, `src/testflow/`, hoặc `tests/`, nên baseline chưa chứng minh TestFlow CLI chạy được.
- Tính năng chưa hoàn thành có mức ưu tiên cao nhất sau tác vụ tài liệu: `tf-001` - Create installable Python CLI skeleton.
- Sự cố chặn hiện tại: Bash không chạy trong sandbox Windows vì WSL chưa có distro. Dùng `init.ps1` trong môi trường hiện tại.

## Nhật ký Phiên

### Phiên 001 - 2026-06-27

- Mục tiêu: Chuyển bộ tài liệu quy trình từ template chung sang trạng thái phù hợp với project TestFlow hiện tại.
- Đã hoàn thành:
  - Đọc `README.md` và xác nhận TestFlow là execution-guided unit test orchestrator cho Python/pytest.
  - Phát hiện các artifact chuẩn ban đầu bị thiếu vì file import có hậu tố ` (1)`.
  - Tạo/cập nhật artifact chuẩn không hậu tố: `feature_list.json`, `claude-progress.md`, `init.sh`, `init.ps1`, `CLAUDE.md`, `session-handoff.md`, `clean-state-checklist.md`, `quality-document.md`, `evaluator-rubric.md`.
  - Xoá các file trùng có hậu tố ` (1)` sau khi tạo bản canonical không hậu tố.
  - Thay feature list mẫu app chat bằng roadmap TestFlow MVP.
- Xác minh đã chạy:
  - `pwd` -> `D:\TestFlow`
  - `git -c safe.directory=D:/TestFlow log --oneline -5` -> `9df7224 Update README.md`, `bddd6f7 Initial commit`
  - Bash baseline -> thất bại do WSL chưa có distro; đây là blocker môi trường cho Bash.
  - `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1` -> exit 0; docs-only baseline passed; implementation scaffold not present yet.
- Bằng chứng đã ghi lại:
  - `feature_list.json` có `ops-001` cho tác vụ tài liệu và các feature `tf-001` đến `tf-008` cho MVP TestFlow.
  - `quality-document.md` ghi rõ repo hiện là docs/product-spec baseline, chưa có implementation scaffold.
- Commit: chưa tạo được. `git add` trong sandbox thất bại vì không tạo được `.git/index.lock`; yêu cầu chạy ngoài sandbox bị từ chối.
- Tệp hoặc artifact đã cập nhật:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `feature_list.json`
  - `claude-progress.md`
  - `init.sh`
  - `init.ps1`
  - `clean-state-checklist.md`
  - `evaluator-rubric.md`
  - `quality-document.md`
  - `session-handoff.md`
  - `index.md`
- Rủi ro đã biết hoặc vấn đề chưa được giải quyết:
  - Chưa có package Python, CLI, agents, examples, hoặc tests.
  - Bash path chưa xác minh được trong sandbox hiện tại vì WSL chưa được cài distro.
  - Git trong sandbox cần `-c safe.directory=D:/TestFlow` hoặc cấu hình safe.directory ngoài repo.
  - Thay đổi tài liệu chưa được commit vì quyền ghi `.git` bị chặn.
- Bước tốt nhất tiếp theo: triển khai `tf-001` bằng cách thêm `pyproject.toml`, `src/testflow/`, CLI entry point, smoke tests, rồi cập nhật `init.ps1`/`init.sh` để chạy pytest thật.
