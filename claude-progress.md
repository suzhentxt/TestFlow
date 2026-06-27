# Nhật ký Tiến độ

## Trạng thái Đã xác minh Hiện tại

- Thư mục gốc kho lưu trữ: `D:\TestFlow`
- Product spec hiện tại: `README.md`
- Đường dẫn khởi động/xác minh chuẩn trên Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1`
- Đường dẫn khởi động/xác minh chuẩn trên Bash: `./init.sh`
- Phạm vi baseline hiện tại: process validation + `.venv` bootstrap + dependency install + pytest khi Python có sẵn. Repo đã có `testflow/state.py` và `tests/test_state.py`, nhưng chưa có `pyproject.toml` hoặc CLI.
- Tính năng chưa hoàn thành có mức ưu tiên cao nhất sau tác vụ tài liệu: `tf-001` - Create installable Python CLI skeleton.
- Sự cố chặn hiện tại: `.venv` chạy được trong môi trường Windows thật và baseline PowerShell pass khi chạy ngoài sandbox. Trong sandbox mặc định của Codex, `.venv` Python không truy cập được base interpreter dưới `C:\Users`. Bash không chạy trong sandbox Windows vì WSL chưa có distro.

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
- Bước tốt nhất tiếp theo: tiếp tục `tf-001` bằng cách thêm `pyproject.toml`, CLI entry point, và smoke tests; khi Codex cần chạy Python trong `.venv`, dùng approval ngoài sandbox vì base interpreter nằm dưới `C:\Users`.

### Phiên 002 - 2026-06-27

- Mục tiêu: Chuẩn hóa toàn bộ lệnh Python của repo để chạy qua `.venv`.
- Đã hoàn thành:
  - Cập nhật `init.ps1` để tạo `.venv` nếu thiếu, cài `requirements.txt`, cài package editable nếu có `pyproject.toml`, và chạy pytest bằng `.\.venv\Scripts\python.exe`.
  - Cập nhật `init.sh` tương tự cho `.venv/bin/python` hoặc `.venv/Scripts/python.exe`.
  - Cập nhật README development commands, AGENTS/CLAUDE rules, checklist, handoff, và feature baseline để không dùng Python/pip/pytest global ngoài bước bootstrap.
- Xác minh đã chạy:
  - `.\.venv\Scripts\python.exe -c "import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)"` chạy ngoài sandbox -> xác nhận `.venv` dùng `D:\TestFlow\.venv` và base `C:\Users\hautt\AppData\Local\Programs\Python\Python310`.
  - `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1` chạy ngoài sandbox -> exit 0; cài dependencies trong `.venv`; `tests/test_state.py` pass.
  - `bash ./init.sh` -> thất bại do WSL chưa có distro.
- Blocker:
  - Python trong `.venv` cần chạy ngoài sandbox nếu command cần truy cập base interpreter dưới `C:\Users`.
  - Bash path vẫn cần WSL distro thật để xác minh.
