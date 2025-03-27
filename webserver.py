import http.server
import socketserver
import threading
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from http import HTTPStatus
import json

PORT = 8000
WATCHED_FILE = "index.html"

LIVE_RELOAD_SCRIPT = """
<script>
(function() {
    function checkForChanges() {
        fetch("/reload")
            .then(response => response.json())
            .then(data => {
                if (!window.lastModified) {
                    window.lastModified = data.timestamp;
                } else if (window.lastModified !== data.timestamp) {
                    location.reload();
                }
            })
            .catch(console.error);
    }
    setInterval(checkForChanges, 1000);
})();
</script>
"""


class ChangeHandler(FileSystemEventHandler):
    """Watches for changes in index.html and updates a timestamp."""
    def on_modified(self, event):
        if event.src_path.endswith(WATCHED_FILE):
            global last_modified
            last_modified = time.time()


class LiveReloadHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler injecting live reload into index.html."""

    def do_GET(self):
        if self.path == "/reload":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"timestamp": last_modified}).encode("utf-8"))
            return

        # Serve index.html with injected script
        if self.path == "/" or self.path == f"/{WATCHED_FILE}":
            try:
                with open(WATCHED_FILE, "r", encoding="utf-8") as f:
                    content = f.read()

                # Inject script before `</body>` if it exists, otherwise append
                if "</body>" in content:
                    content = content.replace("</body>", LIVE_RELOAD_SCRIPT + "</body>")
                else:
                    content += LIVE_RELOAD_SCRIPT

                self.send_response(HTTPStatus.OK)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                return

        # Serve other static files normally
        super().do_GET()


def start_server():
    """Start the HTTP server."""
    with socketserver.TCPServer(("", PORT), LiveReloadHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()


def start_watcher():
    """Start a file watcher for index.html."""
    observer = Observer()
    handler = ChangeHandler()
    observer.schedule(handler, ".", recursive=False)
    observer.start()
    return observer


# Track last modified time
last_modified = time.time()

if __name__ == "__main__":
    observer = start_watcher()
    try:
        start_server()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
