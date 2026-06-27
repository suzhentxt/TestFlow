# CLAUDE.md

Bạn đang làm việc trong repo TestFlow, một execution-guided unit test orchestrator. Ưu tiên của phiên là tính liên tục, xác minh thật, và artifact rõ ràng hơn tốc độ sinh mã.

## Vòng lặp Vận hành

Ở đầu mỗi phiên:

1. Chạy `pwd` và xác nhận đang ở `D:\TestFlow` hoặc root repo tương ứng.
2. Đọc `README.md` để hiểu sản phẩm hiện tại.
3. Đọc `claude-progress.md`.
4. Đọc `feature_list.json` và chọn feature chưa `passing` có priority nhỏ nhất.
5. Xem commit gần đây bằng `git log --oneline -5`.
6. Chạy baseline:
   - PowerShell: `powershell -NoProfile -ExecutionPolicy Bypass -File ./init.ps1`
   - Bash: `./init.sh`
7. Nếu baseline hỏng, sửa hoặc ghi blocker trước khi làm feature mới.

## Quy tắc

- Một feature active tại một thời điểm.
- Không tuyên bố hoàn thành nếu chưa có command xác minh và bằng chứng.
- Không viết lại feature list để che trạng thái chưa xong.
- Không xóa hoặc làm yếu test chỉ để trạng thái có vẻ passing.
- Không sửa production code khi nhiệm vụ chỉ là repair generated tests.
- Sử dụng artifact repo như hệ thống ghi chép chính.

## Tệp Bắt buộc

- `feature_list.json`
- `claude-progress.md`
- `init.ps1`
- `init.sh`
- `quality-document.md`
- `evaluator-rubric.md`
- `clean-state-checklist.md`
- `session-handoff.md`

## Cổng Hoàn thành

Một feature chỉ có thể chuyển sang `passing` sau khi xác minh cần thiết thành công và kết quả được ghi lại trong artifact repo. Với repo hiện tại, baseline chỉ chứng minh tài liệu/harness hợp lệ; nó chưa chứng minh CLI TestFlow chạy được vì implementation scaffold chưa tồn tại.

## Trước khi Dừng

1. Chạy baseline.
2. Cập nhật tiến độ.
3. Cập nhật trạng thái feature.
4. Ghi rõ phần còn hỏng hoặc chưa xác minh.
5. Commit khi repo an toàn để phiên sau tiếp tục.
