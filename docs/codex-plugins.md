# Recommended Codex Plugins

This document records the Codex plugins that are useful for maintaining Easy ML Platform. They are optional for ordinary users of the app, but helpful for repository maintenance, release checks, and documentation work.

## 中文

### 优先下载

- **GitHub**：管理 Issues、Pull Requests、Actions、Release、labels、milestone 和 branch protection。日常维护和发版都优先使用它。
- **Browser**：打开本地 Django 页面，做 UI 烟测、移动端布局检查、截图、语言切换验证和首次使用流程检查。
- **Codex Security**：公开仓库和发布新版本前做安全扫描，重点检查密钥、token、危险配置、路径泄露和不应提交的文件。
- **Spreadsheets**：检查 CSV/Excel 示例数据、导入导出、UTF-8/UTF-8-SIG、中文列名和数据模板。

### 可选下载

- **Documents**：以后需要正式用户手册、课程报告或更完整的说明文档时再使用。
- **Google Drive**：只有在需要同步项目说明、测试数据或演示文档到 Google Drive 时再使用。

### 暂不建议

- **Gmail**、**Google Calendar**：和当前项目维护关系不大。
- **LaTeX**、**Presentations**、**Zotero**：只有在写论文、PPT 或管理参考文献时才需要。

### 默认使用方式

- 日常维护：GitHub + Browser。
- 发版前检查：GitHub + Codex Security + Browser。
- 示例数据和导入导出检查：Spreadsheets + Browser。
- 文档升级：Documents 可选。

## English

### Recommended first

- **GitHub**: Manage Issues, Pull Requests, Actions, Releases, labels, milestones, and branch protection.
- **Browser**: Open the local Django UI, run UI smoke tests, check responsive layouts, update screenshots, and verify language switching.
- **Codex Security**: Run pre-release checks for secrets, tokens, risky configuration, path leaks, and files that should not be committed.
- **Spreadsheets**: Check CSV/Excel examples, import/export behavior, UTF-8/UTF-8-SIG files, Chinese column names, and data templates.

### Optional

- **Documents**: Useful later for a formal user manual, course report, or more polished documentation.
- **Google Drive**: Useful only if project notes, test data, or demo documents need to be synced through Google Drive.

### Not needed for now

- **Gmail** and **Google Calendar** are not relevant to this repository's maintenance workflow.
- **LaTeX**, **Presentations**, and **Zotero** are only needed for papers, slide decks, or reference management.

### Default workflow

- Daily maintenance: GitHub + Browser.
- Release checks: GitHub + Codex Security + Browser.
- Example data and import/export checks: Spreadsheets + Browser.
- Documentation upgrades: Documents when needed.
