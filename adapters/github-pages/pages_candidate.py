"""Fingerprint a static Pages site and smoke-test a page over HTTP. Python 3.9+."""

import argparse
import functools
import hashlib
import os
import re
import stat
import tempfile
import threading
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote
from urllib.request import ProxyHandler, build_opener


def raise_walk_error(error):
    raise error


def site_digest(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("The site folder must be a real directory.")
    index = root / "index.html"
    if not index.is_file() or index.stat().st_size == 0:
        raise ValueError("A nonempty index.html is required.")
    fingerprint = hashlib.sha256(b"pages-public-tree-v1\0")
    for directory, folders, files in os.walk(root, onerror=raise_walk_error):
        folders.sort()
        for name in sorted(folders + files):
            path = Path(directory) / name
            key = path.relative_to(root).as_posix()
            info = path.lstat()
            if name.startswith("."):
                raise ValueError("Excluded hidden path: " + key)
            if stat.S_ISDIR(info.st_mode):
                record = b"D\0"
            elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                content = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        content.update(chunk)
                record = b"F\0" + content.digest()
            else:
                raise ValueError("Unsupported link or special file: " + key)
            fingerprint.update(key.encode("utf-8") + b"\0" + record)
    return fingerprint.hexdigest()


class PageText(HTMLParser):
    """Collect body text, excluding executable or inert content."""
    def __init__(self):
        super().__init__()
        self.in_body = False
        self.excluded = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
        if tag in ("script", "style", "template", "noscript"):
            self.excluded += 1

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
        if tag in ("script", "style", "template", "noscript"):
            self.excluded = max(0, self.excluded - 1)

    def handle_data(self, data):
        if self.in_body and not self.excluded:
            self.parts.append(data)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def smoke(root, base, route, marker, serve, digest):
    if not re.fullmatch(r"/(?:[A-Za-z0-9._~-]+/)*", base) or any(
        part in (".", "..") for part in base.split("/")
    ):
        raise ValueError("Use a base path such as / or /repo-name/.")
    if (route.startswith("/") or any(c in route for c in "?#%\\") or
            any(part in (".", "..") for part in route.split("/"))):
        raise ValueError("Use a relative route, e.g. guide/ or index.html.")
    target_file = root / route
    if target_file.is_dir():
        target_file = target_file / "index.html"
    if not target_file.is_file():
        raise ValueError("The smoke route must resolve to a published file.")
    if not marker.strip():
        raise ValueError("Provide the expected rendered HTML body text.")
    with tempfile.TemporaryDirectory() as tmp:
        served = root
        if base != "/":
            served = Path(tmp)
            mount = served / base.strip("/")
            mount.parent.mkdir(parents=True, exist_ok=True)
            mount.symlink_to(root.resolve(), target_is_directory=True)
        handler = functools.partial(QuietHandler, directory=str(served))
        with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                homepage = "http://127.0.0.1:" + str(server.server_port) + base
                target = homepage + quote(route, safe="/")
                client = build_opener(ProxyHandler({}))
                with client.open(target, timeout=10) as response:
                    if response.status != 200 or response.headers.get_content_type() != "text/html":
                        raise ValueError("The selected route must return HTML and status 200.")
                    parser = PageText()
                    parser.feed(response.read().decode("utf-8"))
                if " ".join(marker.split()) not in " ".join(" ".join(parser.parts).split()):
                    raise ValueError("Expected text missing from the static HTML body.")
                print("HTTP smoke passed:", route, flush=True)
                print("content_sha256=" + digest, flush=True)
                if serve:
                    print("Preview in browser:", homepage, "(Ctrl+C to stop)", flush=True)
                    try:
                        thread.join()
                    except KeyboardInterrupt:
                        pass
            finally:
                server.shutdown()
                thread.join()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--contains", required=True)
    parser.add_argument("--expect", metavar="SHA256")
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    try:
        digest = site_digest(args.directory)
        if args.expect is not None and args.expect != digest:
            raise ValueError("Public content differs from the approved SHA-256.")
        smoke(args.directory, args.base, args.route, args.contains, args.serve, digest)
    except (OSError, ValueError) as exc:
        parser.exit(1, "Pages candidate: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
