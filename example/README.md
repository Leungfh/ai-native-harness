# 本地演练：给发布说明生成器接入检查

示例程序把版本和变更列表生成 Markdown。用一个临时副本依次观察三种结果：配置尚未接入、业务测试和构建通过、回归导致测试失败。以下命令从解压后的套件根目录开始，使用 Python 3.9 或更高版本。演练文件只复制到新建的临时目录。

## 1. 建立副本，观察空配置

**macOS、Linux 或 Git Bash**

```bash
demo_dir="$(mktemp -d)"
cp -R repo/. "$demo_dir/"
python3 "$demo_dir/scripts/harness.py" doctor
python3 "$demo_dir/scripts/harness.py" check
```

**Windows PowerShell**

```powershell
$demoDir = Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString())
New-Item -ItemType Directory $demoDir | Out-Null
Get-ChildItem -Path repo -Force | Copy-Item -Destination $demoDir -Recurse -Force
py -3 "$demoDir/scripts/harness.py" doctor
py -3 "$demoDir/scripts/harness.py" check
```

`doctor` 检查核心文件存在且有内容，以及 JSON 配置格式。`check` 此时会列出未接入的 lint、test、build，返回退出码 2。在真实项目中，先确定可复现的已有命令，再填写这些位置。

## 2. 接入示例，得到真实产物

**macOS、Linux 或 Git Bash**

```bash
cp example/harness.config.json example/release_note.py example/test_release_note.py "$demo_dir/"
python3 "$demo_dir/scripts/harness.py" check
cat "$demo_dir/RELEASE-NOTE.example.md"
```

**Windows PowerShell**

```powershell
Copy-Item example/harness.config.json,example/release_note.py,example/test_release_note.py -Destination $demoDir
py -3 "$demoDir/scripts/harness.py" check
Get-Content "$demoDir/RELEASE-NOTE.example.md" -Encoding utf8
```

预期输出包括 4 项业务测试通过，以及一份含有 `# v0.2.0`、`- 新增导出` 和 `- 修正标题` 的 Markdown 文件。配置中的 `@python` 启动当前解释器。每个数组元素都是一个单独的命令参数，路径和文案可包含空格。每个命令都从仓库根目录启动。

## 3. 引入回归，再恢复

在临时副本的 `release_note.py` 中将 `f"- {item}"` 改为 `f"1. {item}"`，重新运行上一步的 `check` 命令。两项格式测试的失败信息会显示预期和实际字符串的差别，检查返回非零，并停在 test 阶段。之前生成的 Markdown 属于上一次成功构建。把这处改动恢复，再次运行，4 项测试会重新通过。PR 中应该引用本次提交的运行记录和产物。

## 真实项目如何替换

打开工作仓库的 `harness.config.json`，将示例的命令替换成仓库已验证的入口。例：使用 npm、且项目脚本名确实为 lint/test/build 的仓库，可以分别填写 `[["npm","ci"]]`、`[["npm","run","lint"]]`、`[["npm","test"]]` 和 `[["npm","run","build"]]`。在 GitHub Actions 中先按项目约定准备 Node 等运行时和版本，确保测试命令适合非交互环境。多包仓库可引用根目录聚合脚本或在列表里逐条写入各包检查。管道、变量展开等 shell 语法请放在项目已有脚本里，并显式调用它。

setup 可以为空。test 至少需要一条实际验证项目行为的命令，建议使用明确的测试入口，并确认日志显示发现了预期用例。lint 或 build 确实不适用时，将该字段设为 `{"skip_reason":"具体依据"}`。审查者需确认命令有业务断言、覆盖变更范围，并检查跳过理由。GitHub 示例工作流仅执行这些检查，首次接入时将运行链接贴到 PR。
