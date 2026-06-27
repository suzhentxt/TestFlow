# TestFlow Process Docs

Các tài liệu này là harness vận hành cho agent làm việc dài hạn trên TestFlow. `README.md` vẫn là product spec chính; các file dưới đây giữ trạng thái triển khai, chất lượng, xác minh, và bàn giao.

## Artifact Chính

- [AGENTS.md](./AGENTS.md) - hướng dẫn bắt buộc cho coding agents.
- [CLAUDE.md](./CLAUDE.md) - biến thể ngắn cho Claude Code.
- [claude-progress.md](./claude-progress.md) - nhật ký phiên và trạng thái đã xác minh.
- [feature_list.json](./feature_list.json) - nguồn sự thật cho roadmap và trạng thái feature.
- [init.ps1](./init.ps1) - baseline Windows/PowerShell hiện tại.
- [init.sh](./init.sh) - baseline Bash tương đương.
- [quality-document.md](./quality-document.md) - snapshot chất lượng theo domain/lớp kiến trúc.
- [evaluator-rubric.md](./evaluator-rubric.md) - rubric chấp nhận feature.
- [clean-state-checklist.md](./clean-state-checklist.md) - checklist trước khi kết thúc phiên.
- [session-handoff.md](./session-handoff.md) - bàn giao ngắn gọn cho phiên sau.

## Trạng thái Hiện tại

- Repo hiện là docs/product-spec baseline cho TestFlow.
- Implementation package chưa tồn tại.
- Baseline PowerShell kiểm tra tài liệu và JSON; khi `tf-001` hoàn thành, baseline phải chuyển sang install + pytest thật.
