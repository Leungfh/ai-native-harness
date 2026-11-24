#!/usr/bin/env python3
"""Run the project's declared checks with Python 3.9+ and no extra packages."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
STAGES = ("setup", "lint", "test", "build")
CORE_FILES = ("AGENTS.md", "docs/harness/PROJECT.md", "docs/harness/SPEC.md",
              "docs/harness/RELEASE.md")


def load_config():
    path = ROOT / "harness.config.json"
    with path.open(encoding="utf-8-sig") as source:
        config = json.load(source)
    expected_keys = {"schema_version", *STAGES}
    if not isinstance(config, dict) or set(config) != expected_keys:
        raise ValueError("配置需要且仅接受 schema_version、setup、lint、test 和 build 五项。")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("schema_version 应为整数 1。")
    for name in STAGES:
        stage = config[name]
        if isinstance(stage, dict) and name in ("lint", "build"):
            reason = stage.get("skip_reason")
            if set(stage) != {"skip_reason"} or not isinstance(reason, str) or not reason.strip():
                raise ValueError(f"{name} 的 skip_reason 应为有内容的理由。")
            continue
        if not isinstance(stage, list):
            raise ValueError(f"{name} 应为参数数组组成的列表，如 [[\"npm\", \"test\"]]。")
        for number, argv in enumerate(stage, start=1):
            if (not isinstance(argv, list) or not argv
                    or not all(isinstance(arg, str) and "\x00" not in arg for arg in argv)
                    or not argv[0].strip()):
                raise ValueError(f"{name} 第 {number} 条命令需提供可执行程序名及有效字符串参数。")
    return config


def doctor(config):
    missing = [name for name in CORE_FILES
               if not (ROOT / name).is_file() or not (ROOT / name).stat().st_size]
    if missing:
        raise ValueError("缺少文件或文件为空：" + "、".join(missing))
    print("仓库基础文件与配置结构检查通过。此命令只检查文件和配置格式。")
    for name in STAGES:
        if name != "setup" and config[name] == []:
            print(f"  待接入 {name}：运行 check 前请配置。")
    return 0


def check(config):
    missing = [name for name in STAGES if name != "setup" and config[name] == []]
    if missing:
        raise ValueError("项目检查尚未接入：" + "、".join(missing)
                         + "。请在 harness.config.json 填写项目真实命令。")
    for name in STAGES:
        stage = config[name]
        if isinstance(stage, dict):
            print(f"[{name}] 不适用：{stage['skip_reason']}", flush=True)
            continue
        for number, argv in enumerate(stage, start=1):
            program = argv[0]
            if program == "@python":
                program = sys.executable
            elif os.name == "nt" and os.path.basename(program) == program:
                # Resolve PATH launchers such as npm.cmd on Windows.
                program = shutil.which(program) or program
            print(f"[{name} {number}/{len(stage)}] {argv[0]}", flush=True)
            try:
                result = subprocess.run([program, *argv[1:]], cwd=ROOT, check=False)
            except FileNotFoundError:
                print(f"[{name}] 找不到程序 {argv[0]}。请核对工具链或工作流的环境准备步骤。",
                      file=sys.stderr)
                return 127
            except OSError as error:
                print(f"[{name}] 程序启动失败：{error}", file=sys.stderr)
                return 126
            if result.returncode:
                print(f"[{name}] 命令退出码 {result.returncode}，停止后续阶段。", file=sys.stderr)
                return result.returncode if result.returncode > 0 else 128 - result.returncode
    print("已配置的项目检查全部通过。")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("doctor", "check"),
                        help="doctor 检查仓库基础文件和配置；check 执行项目命令")
    action = parser.parse_args().action
    try:
        config = load_config()
        return doctor(config) if action == "doctor" else check(config)
    except (OSError, ValueError) as error:
        print(f"Harness：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
