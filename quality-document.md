# Tài liệu Chất lượng

Snapshot này mô tả chất lượng hiện tại của TestFlow theo tài liệu sản phẩm và trạng thái repo thực tế. Điểm số đánh giá phần đã tồn tại trong repo, không đánh giá tham vọng trong README.

**Tần suất cập nhật:** sau mỗi feature `passing`, khi baseline thay đổi, hoặc trước khi bàn giao phiên lớn.

**Thang điểm:**

- **A**: Xác minh chạy thật, kiến trúc rõ, test ổn định, agent có thể tiếp tục không cần đoán.
- **B**: Baseline chạy, tài liệu rõ, còn thiếu nhỏ hoặc implementation chưa phủ đủ.
- **C**: Hoạt động một phần, có khoảng trống đáng kể hoặc xác minh chưa đủ.
- **D**: Chưa hoạt động hoặc chưa có artifact triển khai.

## Domain Sản phẩm

| Domain | Điểm | Xác minh | Khả năng đọc của Agent | Độ ổn định Test | Khoảng trống chính | Cập nhật lần cuối |
| --- | --- | --- | --- | --- | --- | --- |
| Product spec / README | B | Đã đọc thủ công | Cao: mô tả rõ problem, architecture, agents, MVP scope | N/A | Chưa ràng buộc với implementation thật | 2026-06-27 |
| Repo operating harness | B | PowerShell baseline passed | Cao sau khi chuẩn hóa file không hậu tố | N/A | Bash chưa xác minh được trong sandbox WSL-less | 2026-06-27 |
| CLI package | D | Chưa có | Trung bình: README mô tả lệnh mong muốn | Chưa có test | Thiếu `pyproject.toml`, entry point, CLI module | 2026-06-27 |
| Analyzer Agent | D | Chưa có | Trung bình: README mô tả input/output | Chưa có test | Thiếu parser AST và fixtures | 2026-06-27 |
| Runtime state / Planner | D | Chưa có | Cao ở mức spec | Chưa có test | Thiếu model state và heuristic planner | 2026-06-27 |
| Runner Agent / pytest feedback | D | Chưa có | Cao ở mức spec | Chưa có test | Thiếu subprocess runner và parser pytest output | 2026-06-27 |
| Test generation / repair | D | Chưa có | Trung bình: cần interface LLM cụ thể | Chưa có test | Thiếu deterministic seams, generated file policy, repair rules | 2026-06-27 |
| Coverage / verifier / report | D | Chưa có | Cao ở mức spec | Chưa có test | Thiếu coverage.xml parser, assertion-quality checks, report renderer | 2026-06-27 |

## Lớp Kiến trúc

| Lớp | Điểm | Thực thi Ranh giới | Khả năng đọc của Agent | Khoảng trống chính | Cập nhật lần cuối |
| --- | --- | --- | --- | --- | --- |
| Documentation layer | B | README và process docs đã chuẩn hóa | Cao | Cần cập nhật sau khi có code thật | 2026-06-27 |
| Package/CLI layer | D | Chưa tồn tại | Dễ tạo từ `tf-001` | Thiếu package Python | 2026-06-27 |
| Orchestrator/state layer | D | Chưa tồn tại | Spec rõ trong README | Thiếu state model, planner, loop | 2026-06-27 |
| Agent layer | D | Chưa tồn tại | Spec rõ theo từng agent | Thiếu analyzer, edge case, generator, runner, repair, coverage, verifier | 2026-06-27 |
| Execution/reporting layer | D | Chưa tồn tại | Spec rõ | Thiếu pytest execution, coverage parsing, final report | 2026-06-27 |
| Test suite | D | Chưa tồn tại | N/A | Thiếu `tests/`, fixtures, smoke tests | 2026-06-27 |

## Lịch sử Thay đổi

### 2026-06-27

- Thay đổi: Chuyển quality document từ template document-Q&A sang TestFlow.
- Domain được nâng cấp: Documentation layer và repo operating harness.
- Domain bị hạ cấp/ghi rõ: Tất cả domain implementation đang là D vì chưa có code.
- Khoảng trống mới được xác định: cần `tf-001` để tạo package Python/CLI và chuyển baseline từ docs-only sang pytest thật.
- Khoảng trống đã đóng: trạng thái chất lượng không còn mâu thuẫn với README.
