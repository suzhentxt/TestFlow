# Bàn giao Phiên

## Đang Hoạt động Hiện tại

- Những gì đang hoạt động:
  - `README.md` mô tả rõ TestFlow là execution-guided unit test orchestrator.
  - Bộ artifact quy trình đã được chuyển sang TestFlow và có bản canonical không hậu tố.
  - `feature_list.json` đã có roadmap MVP từ `ops-001` đến `tf-008`.
- Xác minh nào thực sự đã chạy:
  - `pwd` xác nhận root là `D:\TestFlow`.
  - `git -c safe.directory=D:/TestFlow log --oneline -5` đọc được commit gần nhất.
  - Bash baseline đã thử nhưng thất bại vì WSL chưa cài distro.
  - `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1` exit 0; docs-only baseline passed.

## Thay đổi Trong Phiên này

- Mã hoặc hành vi đã thêm:
  - Không thêm implementation TestFlow.
  - Thêm baseline script `init.ps1` và `init.sh` cho trạng thái docs-only hiện tại.
- Thay đổi cơ sở hạ tầng hoặc harness:
  - Chuẩn hóa artifact không hậu tố: `claude-progress.md`, `feature_list.json`, `CLAUDE.md`, `clean-state-checklist.md`, `evaluator-rubric.md`, `quality-document.md`, `session-handoff.md`, `init.sh`.
  - Xoá các file trùng có hậu tố ` (1)`; bản canonical không hậu tố là nguồn sự thật.

## Bị Hỏng hoặc Chưa được Xác minh

- Lỗi đã biết:
  - Repo chưa có Python package, CLI, agents, examples, hoặc tests.
  - Bash path chưa xác minh được trong sandbox này vì `bash` gọi WSL và WSL chưa có distro.
  - Git báo dubious ownership nếu không dùng `-c safe.directory=D:/TestFlow`.
- Đường dẫn chưa được xác minh:
  - `./init.sh` trong môi trường Bash thật.
  - Bất kỳ command README nào như `testflow run ...`, `pytest tests/`, hoặc `pip install -e .` vì implementation chưa tồn tại.
- Rủi ro cho phiên tiếp theo:
  - Đừng đánh dấu feature product nào `passing` cho đến khi có code và test thật.
  - Khi tạo package Python, nhớ nâng baseline từ docs-only sang install + pytest.
  - Thay đổi tài liệu hiện chưa có commit vì sandbox không cho ghi `.git/index.lock` và escalation để `git add` bị từ chối.

## Bước Tốt nhất Tiếp theo

- Tính năng chưa hoàn thành có mức ưu tiên cao nhất: `tf-001` - Create installable Python CLI skeleton.
- Tại sao đây là tính năng tiếp theo: mọi feature TestFlow khác phụ thuộc vào package/CLI và test harness.
- Điều gì được tính là vượt qua:
  - Có `pyproject.toml`, `src/testflow/`, entry point `testflow`.
  - `testflow --help` chạy được.
  - Có tests tối thiểu cho CLI.
  - `init.ps1` và `init.sh` chạy install/test thật.
- Điều gì không được thay đổi trong bước đó:
  - Không làm yếu process docs hoặc bỏ yêu cầu bằng chứng.
  - Không triển khai LLM generation trước khi có CLI/state nền.

## Lệnh

- Khởi động Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1`
- Khởi động Bash: `./init.sh`
- Xem Git trong sandbox: `git -c safe.directory=D:/TestFlow status --short`
- Debug tập trung kế tiếp: sau `tf-001`, dùng `python -m pytest tests/` và `testflow --help`
