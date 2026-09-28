import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from xdan_jev_plugin.cli import chat


def test_real_http_wire():
    captured = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            captured.append(
                (
                    self.path,
                    json.loads(self.rfile.read(int(self.headers["Content-Length"]))),
                )
            )
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"choices": [{"message": {"content": "ok"}}]}')

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    body = {
        "mode": "auto",
        "effort": "high",
        "messages": [{"role": "user", "content": "hello"}],
    }
    try:
        answer = chat(f"http://127.0.0.1:{server.server_port}", body)
        assert answer["choices"][0]["message"]["content"] == "ok"
        assert captured == [("/v1/chat/completions", body)]
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_url_scheme():
    with pytest.raises(ValueError):
        chat("file:///tmp/a", {})


@pytest.mark.parametrize("command", ["verify", "prepare", "chat", "serve"])
def test_cli_dispatch(tmp_path, monkeypatch, capsys, command):
    from xdan_jev_plugin import cli

    calls = []
    monkeypatch.setattr(
        cli, "verify", lambda root: calls.append(str(root)) or {"verified": True}
    )
    monkeypatch.setattr(cli, "prepare", lambda output, base: {"verified": True})
    monkeypatch.setattr(
        cli, "chat", lambda url, body, timeout: {"answer": body["text"]}
    )
    monkeypatch.setattr(cli.subprocess, "call", lambda args: calls.append(args) or 0)
    request = tmp_path / "request.json"
    request.write_text('{"text":"hello"}')
    argv = {
        "verify": ["--model-dir", str(tmp_path)],
        "prepare": ["--output", str(tmp_path)],
        "chat": ["--request", str(request)],
        "serve": ["--model-dir", str(tmp_path)],
    }
    monkeypatch.setattr(cli.sys, "argv", ["xdan-jev", command, *argv[command]])
    if command == "serve":
        with pytest.raises(SystemExit) as error:
            cli.main()
        assert error.value.code == 0
        assert calls[1][1] == str(tmp_path / "serve.py")
        assert calls[1][5] == "127.0.0.1"
    else:
        cli.main()
        assert json.loads(capsys.readouterr().out)


def test_cli_bad_json(tmp_path, monkeypatch, capsys):
    from xdan_jev_plugin import cli

    request = tmp_path / "bad.json"
    request.write_text("invalid")
    monkeypatch.setattr(
        cli.sys, "argv", ["xdan-jev", "chat", "--request", str(request)]
    )
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1
    assert "xdan-jev:" in capsys.readouterr().err
