# 项目卡

| 项 | 已核实事实 |
| --- | --- |
| 仓库 / 主分支 | Leungfh/ai-native-harness，main；初始基线 90e09af5fc40194bbca00cd2909f531d25f73930 |
| 用途 | 为业务仓库提供可验证的 Harness 模板、示例、工作簿与分发工具。 |
| 负责人 | 待仓库所有者指定产品、代码和发布负责人。 |
| 运行时 | Python 3.9+ 标准库；本地实测 Python 3.11.9；无依赖锁文件。 |
| 源码 / 模板 / 测试 | tools/kit.py；repo/；tests/ 与 example/。 |
| 交付与产物 | GitHub 源码；`python tools/kit.py build --out build/dist` 生成版本 ZIP。 |
| CI | `.github/workflows/harness-ci.yml`，PR、merge queue 或手动触发；远端运行结果待验证。 |
| 部署与恢复 | 推送仓库由仓库所有者审查；版本包按 MAINTENANCE.md 验证；恢复用 Git revert 或使用之前经过验证的包。负责人和正式发布环境待确认。 |

## 可复现命令

在仓库根目录运行 `python scripts/harness.py doctor` 和 `python scripts/harness.py check`。检查运行集成测试、清单校验及 ZIP 构建；测试覆盖冲突保护、文件篡改和恢复以及示例行为。独立静态检查尚未配置，理由见 harness.config.json。模板分发清单及校验摘要保留在 KIT-FILES.txt 和 MANIFEST.sha256，根目录接入文件不属于模板包。

## 发布证据

版本包的正式发布、CI、审查责任人和生产观察窗口待仓库所有者确定；尚未建立 GitHub Release 或生产部署流程。参见 MAINTENANCE.md 和 docs/harness/RELEASE.md。
