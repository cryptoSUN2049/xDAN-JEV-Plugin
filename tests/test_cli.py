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
