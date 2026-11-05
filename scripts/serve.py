#!/usr/bin/env python3
"""Preview dist/ at the same subpath as GitHub Pages. Never serves author files."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = '/the-neverlands/'


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT/'dist'), **kwargs)

    def send_head(self):
        path = urlsplit(self.path).path
        if path in ('/', BASE.rstrip('/')):
            self.send_response(302)
            self.send_header('Location',BASE)
            self.end_headers()
            return None
        if not path.startswith(BASE):
            self.send_error(404)
            return None
        self.path = self.path[len(BASE)-1:]
        return super().send_head()


if __name__ == '__main__':
    print(f'Preview: http://127.0.0.1:4173{BASE}',flush=True)
    try:
        ThreadingHTTPServer(('127.0.0.1',4173),Handler).serve_forever()
    except KeyboardInterrupt:
        pass
