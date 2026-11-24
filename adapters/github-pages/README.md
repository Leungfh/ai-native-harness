# 可选发布适配器 · GitHub Pages 静态站点

适用于在 GitHub.com 上发布到 Pages、能够生成可重复构建的 `dist/`、且至少有一条含静态 HTML 正文的可测页面的站点。预演者在浏览器验证关键操作，并记录整棵公开目录的 SHA-256。工作流从同一提交重建，重新执行项目检查，在待上传的目录副本上比较指纹、运行 HTTP 冒烟测试，两者通过才会发布。服务端、数据库和全部页面只在浏览器渲染正文的项目应选择适合其运行方式的适配器。

## 首次接入

1. 将 [pages.yml.example](pages.yml.example) 合入目标仓库的 `.github/workflows/pages.yml`，将 [pages_candidate.py](pages_candidate.py) 合入 `scripts/pages_candidate.py`。通过 PR 审查并合入默认分支。已有发布流程时，合并需要的步骤，保留一个生产入口。
2. 在 `harness.config.json` 接入项目的实际检查与静态构建，输出 `dist/index.html`。需要 Node 等工具链时，在工作流注释处加入现有 CI 已验证的版本设置步骤。项目站点通常部署在 `/<仓库名>/` 下，按实际 Pages 地址设置构建基础路径。工作流示例以 Linux 为运行环境，本地可用 Linux、macOS 或 WSL。
3. 在 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。在 **Settings → Environments → github-pages** 将可部署分支限制为默认分支。若项目约定审批，使用该仓库支持的环境保护规则或已有的审批记录。

## 在 G03 预演候选版本

在干净检出目录选择已审查的默认分支提交。用该版本实际基础路径、关键页面和该页面预期出现的正文替换以下示例值。命令先运行项目测试和构建，再通过本地 HTTP 请求校验所得页面，打印内容摘要并打开本机预览入口。

```bash
git rev-parse HEAD
python3 scripts/harness.py check
python3 scripts/pages_candidate.py dist --base /handbook/ --route guide/ --contains '开始使用' --serve
```

在浏览器打开打印的预览地址，按本版验收标准走一遍使用路径，例如从首页导航进入指南、刷新深层链接，核对页面、样式与图片。记录实际结果与证据，完成后按 Ctrl+C。自动检查要求目标页面返回 HTTP 200 和 HTML，且正文包含指定文字；交互、样式和可访问性由实际验收步骤覆盖。

将 `docs/harness/RELEASE.md` 模板复制为本版发布单或发布 Issue。在默认分支已选定候选提交后，把完整 Git SHA、`content_sha256`、三项冒烟参数、预演人、实际操作和证据追加到**发布 Issue 或独立发布记录分支**，避免为了记录当前 SHA 又产生新的候选提交。可以先在 PR 中放入空发布单，事后再归档本版执行记录。发布负责人核对其余门禁并记录决定，再触发生产发布。

## 发布、观察与回退

| 操作 | 执行与记录 |
| --- | --- |
| 手动发布 | 在 **Actions → Publish static site to GitHub Pages → Run workflow** 选默认分支，从同一条已通过的预演记录复制候选完整 SHA、公开目录摘要、基础路径、相对路由与正文。分支、提交或目录摘要有差异，或 HTTP 断言失败，工作流都会在上传前终止。 |
| 核对制品 | 构建作业把此次构建复制到独立目录，核对摘要并执行 HTTP 测试，然后上传该目录。发布作业只消费该次运行传来的制品名。把工作流运行链接、摘要和实际发布时间追加到原发布记录。摘要不一致时检查依赖锁、产物内嵌时间或配置差异，定位差异后重新预演，保留两次记录。 |
| 观察 | 从运行中的 `github-pages` 环境链接打开线上地址，重复预演的关键操作，深层刷新并检查一个真实样式或脚本资源。按既定观察窗口及阈值记录实测结果，发布负责人填写最终结论。 |
| 回退 | 触发停止条件时，通过回退 PR 撤销故障变更，核对期间其他提交。对回退提交的新 SHA 重新预演、核对摘要并手动发布，追加恢复时间、两次运行、同口径验证结果和后续 Issue。 |

目录指纹覆盖所有相对路径、路径类型及每个常规文件的完整内容，顺序固定。文件时间、目录所有者与压缩封装元数据不参与计算。脚本拒绝隐藏路径、硬链接、符号链接和特殊文件，以使预演范围与默认 Pages 打包范围一致。需要 `.well-known/` 等隐藏路径的项目应调整打包和校验两处，再验证实际上传的完整清单。预演期间保持输出目录固定。构建中写入动态时间且无法稳定重建的项目，可在项目适配器中保存预演产物，并在部署时直接提升该制品。

工作流使用触发时的提交。等待批准或排队期间默认分支前进时，发布负责人核实是否仍需发布该候选，取消过时的运行。需要发布新提交时重新预演并发起。并发组串行处理发布，等待中的运行可被后续请求替换。

GitHub 官方参考：[自定义 Pages 工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)、[选择发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)、[Pages 项目地址](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)、[制品打包版本说明](https://github.com/actions/upload-pages-artifact/releases/tag/v4.0.0)、[工作流并发](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)。
