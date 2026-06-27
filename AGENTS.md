# AGENTS.md

Kho lưu trữ này dành cho TestFlow: một execution-guided unit test orchestrator. Mục tiêu của agent là để lại repo ở trạng thái mà phiên tiếp theo có thể tiếp tục từ artifact trong repo, không cần đoán từ lịch sử chat.

`README.md` là product spec hiện tại. Các artifact vận hành bắt buộc là `feature_list.json`, `claude-progress.md`, `init.sh`, `init.ps1`, `quality-document.md`, `evaluator-rubric.md`, `clean-state-checklist.md`, và `session-handoff.md`.

## Quy trình Khởi động

Trước khi viết mã hoặc sửa tài liệu:

1. Xác nhận thư mục làm việc bằng `pwd`.
2. Đọc `README.md` để nắm mục tiêu sản phẩm TestFlow.
3. Đọc `claude-progress.md` để biết trạng thái đã xác minh mới nhất và bước tiếp theo.
4. Đọc `feature_list.json` và chọn tính năng chưa `passing` có mức ưu tiên cao nhất.
5. Xem lại commit gần đây bằng `git log --oneline -5`. Nếu Git báo dubious ownership trong sandbox, dùng `git -c safe.directory=D:/TestFlow ...` thay vì ghi cấu hình global.
6. Chạy baseline:
   - Windows/PowerShell hiện tại: `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1`
   - Môi trường có Bash: `./init.sh`
7. Nếu baseline thất bại, sửa baseline hoặc ghi blocker trước. Không chồng công việc tính năng mới lên trạng thái khởi đầu bị hỏng.

## Quy tắc Làm việc

- Làm việc trên một tính năng tại một thời điểm.
- Không đánh dấu tính năng `passing` chỉ vì mã đã được thêm vào.
- Không sửa production code để làm cho generated tests pass, trừ khi tính năng đang làm rõ ràng là sửa bug sản phẩm.
- Không làm yếu kiểm tra hoặc thay đổi quy tắc xác minh ngầm trong lúc triển khai.
- Ưu tiên artifact repo lâu bền hơn tóm tắt chat.
- Khi repo chưa có implementation scaffold, chỉ được coi baseline là docs-only; không được tuyên bố TestFlow đã chạy thật.
- Tất cả lệnh Python, pip, pytest, và TestFlow phải chạy qua `.venv`; chỉ dùng Python global để bootstrap `.venv`.

## Artifact Bắt buộc

- `feature_list.json`: nguồn sự thật cho trạng thái tính năng và bằng chứng.
- `claude-progress.md`: nhật ký phiên và trạng thái đã xác minh hiện tại.
- `init.ps1` và `init.sh`: đường dẫn khởi động/xác minh chuẩn cho Windows và Bash.
- `quality-document.md`: snapshot chất lượng theo domain và lớp kiến trúc.
- `evaluator-rubric.md`: rubric chấp nhận trước khi chuyển feature sang `passing`.
- `clean-state-checklist.md`: checklist trước khi kết thúc phiên.
- `session-handoff.md`: bàn giao ngắn gọn khi có trạng thái đáng lưu lại.

## Định nghĩa Hoàn thành

Một tính năng chỉ xong khi tất cả điều sau đúng:

- Hành vi mục tiêu đã được triển khai hoặc tài liệu mục tiêu đã được cập nhật đúng phạm vi.
- Xác minh cần thiết đã thực sự chạy.
- Bằng chứng được ghi lại trong `feature_list.json` hoặc `claude-progress.md`.
- Repo vẫn có thể khởi động lại từ đường dẫn baseline chuẩn.
- Rủi ro, phần chưa xác minh, hoặc blocker còn lại được ghi rõ.

## Cuối Phiên

Trước khi kết thúc phiên:

1. Chạy baseline phù hợp với môi trường.
2. Cập nhật `claude-progress.md`.
3. Cập nhật `feature_list.json`.
4. Cập nhật `session-handoff.md` nếu có thông tin hữu ích cho phiên sau.
5. Kiểm tra `clean-state-checklist.md`.
6. Commit với thông điệp mô tả khi repo ở trạng thái an toàn.
