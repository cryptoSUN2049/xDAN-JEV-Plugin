"""Install, validate, serve and call the pinned research bundle."""

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .bundle import prepare, verify


def chat(url, body, timeout=120):
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must use HTTP or HTTPS")
    request = urllib.request.Request(
        url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body, ensure_ascii=False, allow_nan=False).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser(
        "prepare", help="Download and verify the research model"
    )
    install.add_argument("--output", required=True)
    install.add_argument(
        "--base-dir", help="Optional existing pinned base; hashes must match"
    )
    check = commands.add_parser("verify")
    check.add_argument("--model-dir", required=True)
    serve = commands.add_parser("serve", help="Single-request Transformers CUDA server")
    serve.add_argument("--model-dir", required=True)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=18183)
    serve.add_argument("--model-name", default="xdan-jev-research-r1")
    serve.add_argument(
        "--variant", choices=["seed17", "seed29", "seed43"], default="seed17"
    )
    call = commands.add_parser("chat")
    call.add_argument("--url", default="http://127.0.0.1:18183")
    call.add_argument("--request", type=Path, required=True, help="JSON request file")
    call.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.output, args.base_dir)
        elif args.command == "verify":
            result = verify(args.model_dir)
        elif args.command == "chat":
            result = chat(args.url, json.loads(args.request.read_text()), args.timeout)
        else:
            root = Path(args.model_dir).resolve()
            verify(root)
            raise SystemExit(
                subprocess.call(
                    [
                        sys.executable,
                        str(root / "serve.py"),
                        "--model-dir",
                        str(root),
                        "--host",
                        args.host,
                        "--port",
                        str(args.port),
                        "--model-name",
                        args.model_name,
                        "--variant",
                        args.variant,
                    ]
                )
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, urllib.error.URLError) as exc:
        parser.exit(1, f"xdan-jev: {exc}\n")


if __name__ == "__main__":
    main()
