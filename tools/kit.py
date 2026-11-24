#!/usr/bin/env python3
"""Compare a kit to a target repository, verify a distribution, or build the next one."""

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parent.parent
INVENTORY = "KIT-FILES.txt"
MANIFEST = "MANIFEST.sha256"


def safe_entry(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or path.as_posix() != name
            or ".." in path.parts or name == "." or "\\" in name or ":" in name):
        raise ValueError(f"清单含不适用的相对路径：{name!r}")
    return name


def inventory(root):
    lines = (root / INVENTORY).read_text(encoding="utf-8").splitlines()
    names = [safe_entry(line) for line in lines if line and not line.startswith("#")]
    if (len(set(names)) != len(names) or MANIFEST in names
            or not {INVENTORY, "VERSION", "CHANGELOG.md", "tools/kit.py"}.issubset(names)):
        raise ValueError("清单含重复项、生成项或缺少打包所需文件。")
    return sorted(names)


def read_entry(root, name):
    path = root / name
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"请手工核对符号链接：{name}")
    if not path.is_file():
        raise ValueError(f"缺少常规文件：{name}")
    return path.read_bytes()


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def manifest(files):
    return "".join(f"{digest(blob)}  {name}\n" for name, blob in sorted(files.items())).encode()


def distribution_files(root):
    return {name: read_entry(root, name) for name in inventory(root)}


def verify():
    files = distribution_files(ROOT)
    if manifest(files) != read_entry(ROOT, MANIFEST):
        raise ValueError("至少一项内容或文件清单与发布包不同。")
    print(f"已核对 {len(files)} 个交付文件。")


def build(out):
    # Read only the release inventory, so a working copy can also contain local notes.
    files = distribution_files(ROOT)
    version = files["VERSION"].decode().strip()
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version):
        raise ValueError("VERSION 请使用三段数字，如 1.0.1。")
    if f"## {version} · " not in files["CHANGELOG.md"].decode("utf-8"):
        raise ValueError("CHANGELOG.md 缺少此版小节，示例：## 1.0.1 · YYYY-MM-DD。")
    files[MANIFEST] = manifest(files)
    out.mkdir(parents=True, exist_ok=True)
    archive = out / f"AI-Native-Harness-Kit-v{version}.zip"
    # Link a finished file into place, preserving an existing release of the same name.
    with tempfile.NamedTemporaryFile(dir=out, delete=False) as temp:
        tmp_path = Path(temp.name)
    try:
        with zipfile.ZipFile(tmp_path, "w") as package:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                package.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        try:
            os.link(tmp_path, archive)
        except FileExistsError:
            if digest(archive.read_bytes()) != digest(tmp_path.read_bytes()):
                raise ValueError(f"已有同名且内容不同的发布包。请使用新版本或空输出目录：{archive}")
    finally:
        tmp_path.unlink(missing_ok=True)
    print(f"{archive}\nSHA-256  {digest(archive.read_bytes())}")


def repo_files(kit):
    return {name[5:]: read_entry(kit, name) for name in inventory(kit) if name.startswith("repo/")}


def classify(old, new, local):
    if local == new:
        return "双方已移除" if new is None else "已相同"
    if new is None:
        return "模板已移除·人工评估" if local == old else "模板已移除·保留本地核对"
    if old is None:
        return "可新增" if local is None else "已有同名·人工合并"
    if local is None:
        return "项目已移除·人工评估"
    if local == old:
        return "可更新"
    if old == new:
        return "保留项目定制"
    return "双方有改动·三方合并"


def plan(target, previous):
    target = target.resolve()
    if not target.is_dir():
        raise ValueError(f"目标目录不存在：{target}")
    base = {} if previous is None else repo_files(previous.resolve())
    new = repo_files(ROOT)
    for name in sorted(set(base) | set(new)):
        path = target / name
        # Detect file/directory and parent-symlink collisions before proposing a copy.
        nodes = [p for p in (path, *path.parents) if p != target and target in p.parents]
        if any(p.is_symlink() for p in nodes) or any(
                p.exists() and not p.is_dir() for p in nodes if p != path
        ) or (path.exists() and not path.is_file()):
            state = "路径冲突·人工核对"
        else:
            local = path.read_bytes() if path.is_file() else None
            state = classify(base.get(name), new.get(name), local)
        print(f"{state}\t{name}")
    print("仅比较 repo/ 中的交付路径。请在目标仓库分支上复核适用项并提交差异。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    compare = commands.add_parser("plan", help="查看目标仓库与模板的差异")
    compare.add_argument("target", type=Path)
    compare.add_argument("--previous", type=Path, help="上次采用版本的原始文件包目录")
    pack = commands.add_parser("build", help="按清单构建发布包")
    pack.add_argument("--out", type=Path, required=True)
    commands.add_parser("verify", help="校验解压后的发布包")
    args = parser.parse_args()
    try:
        if args.action == "plan":
            plan(args.target, args.previous)
        elif args.action == "build":
            build(args.out.resolve())
        else:
            verify()
    except (OSError, ValueError) as error:
        print(f"Harness Kit：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
