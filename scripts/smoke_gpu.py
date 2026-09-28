"""Exercise the installed CLI against a ready GPU server (engineering, not quality)."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:18183")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    examples = Path(__file__).resolve().parents[1] / "examples"
    rows = []
    with tempfile.TemporaryDirectory() as temporary:
        request = Path(temporary) / "request.json"
        for mode in ("llm", "auto", "jev"):
            for effort, depth in zip(
                ("minimal", "low", "medium", "high", "max"), (3, 6, 10, 13, 16)
            ):
                body = json.loads((examples / f"{mode}.json").read_text())
                body["effort"] = effort
                request.write_text(json.dumps(body))
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "xdan_jev_plugin.cli",
                        "chat",
                        "--url",
                        args.url,
                        "--request",
                        str(request),
                    ],
                    check=True,
                    text=True,
                    capture_output=True,
                    timeout=180,
                )
                result = json.loads(completed.stdout)
                meta = result["xdan"]
                execution = meta["execution"]
                assert result["choices"][0]["message"]["content"]
                assert meta["resolved_route_depth"] == depth
                assert execution["backbone_instances"] == 1
                if mode == "llm":
                    assert meta["selected_route"] == "llm"
                    assert not execution.get("adapter_executed", False)
                    assert not meta["route_controls_active"]
                elif mode == "jev":
                    assert meta["selected_route"] == "jev"
                    assert execution["adapter_executed"]
                else:
                    assert meta["route_controls_active"]
                    assert meta["effective_route_depth"] == depth
                    if meta["selected_route"] == "jev":
                        assert execution["adapter_executed"]
                        assert execution["jev_prefix_reused"]
                rows.append(
                    {
                        "mode": mode,
                        "effort": effort,
                        "resolved_depth": depth,
                        "selected_route": meta["selected_route"],
                        "adapter_executed": execution.get("adapter_executed", False),
                        "prefix_reused": execution.get("jev_prefix_reused", False),
                        "answer": result["choices"][0]["message"]["content"],
                        "server_wall_seconds": meta["server_wall_seconds"],
                    }
                )
    assert any(r["mode"] == "auto" and r["adapter_executed"] for r in rows)
    report = {
        "passed": True,
        "http_calls": len(rows),
        "scope": "New synthetic smoke examples, not held-out quality or performance benchmark",
        "results": rows,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "http_calls": len(rows)}))


if __name__ == "__main__":
    main()
