# Rubric Evaluator

Sử dụng rubric này sau khi triển khai một feature TestFlow và trước khi chuyển feature sang `passing`.

| Hạng mục | Câu hỏi | Điểm (0-2) | Ghi chú |
| --- | --- | --- | --- |
| Khớp product spec | Hành vi có khớp `README.md` và feature trong `feature_list.json` không? |  |  |
| Execution feedback thật | Feature có chạy command thật, đọc kết quả thật, hoặc ghi rõ vì sao chưa thể không? |  |  |
| State/orchestration | Nếu liên quan planner/agent, state có được cập nhật rõ và next action có giải thích được không? |  |  |
| Không sửa sai phạm vi | Feature có tránh sửa production code khi nhiệm vụ chỉ là generated tests/repair không? |  |  |
| Xác minh | Các kiểm tra bắt buộc có thực sự chạy với bằng chứng lệnh và kết quả không? |  |  |
| Test quality | Test có assertion có nghĩa, không duplicate, không flaky rõ ràng không? |  |  |
| Khả năng bảo trì | Mã/tài liệu có đủ rõ để agent phiên sau tiếp tục không? |  |  |
| Bàn giao | `claude-progress.md`, `feature_list.json`, và `session-handoff.md` có phản ánh trạng thái mới không? |  |  |

## Chấm Điểm

- `0`: Không đạt hoặc chưa có bằng chứng.
- `1`: Đạt một phần, còn rủi ro hoặc thiếu coverage.
- `2`: Đạt đầy đủ với bằng chứng chạy được.

## Cổng Chấp nhận

- Chấp nhận: tổng điểm >= 13 và không có hạng mục 0 ở `Xác minh` hoặc `Bàn giao`.
- Sửa đổi: tổng điểm 9-12 hoặc còn thiếu bằng chứng nhỏ.
- Chặn: tổng điểm < 9, baseline hỏng, hoặc feature tuyên bố `passing` mà chưa chạy xác minh.

## Hành động Tiếp theo Bắt buộc

- Bằng chứng còn thiếu:
- Sửa chữa bắt buộc:
- Artifact cần cập nhật:
- Kích hoạt review tiếp theo:
