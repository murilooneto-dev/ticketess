import sys
import threading
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# pythonw.exe runs with no console: sys.stdout/stderr are None, and the first
# log write (from uvicorn/logging) raises and silently kills the server thread.
# Redirect them to a log file before importing anything that logs.
if sys.stdout is None or sys.stderr is None:
    log_file = open(BASE_DIR / "tray.log", "a", buffering=1, encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file

import httpx
import pystray
import uvicorn
from PIL import Image

from app.config import settings

ICON_PATH = BASE_DIR.parent / "frontend" / "public" / "logo.png"
APP_URL = f"http://localhost:{settings.APP_PORT}"


def load_tray_icon() -> Image.Image:
    source = Image.open(ICON_PATH).convert("RGBA")
    size = max(source.size)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(source, ((size - source.width) // 2, (size - source.height) // 2), source)
    return canvas

server: uvicorn.Server | None = None


def run_server() -> None:
    global server
    config = uvicorn.Config("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=False)
    server = uvicorn.Server(config)
    server.run()


def wait_until_ready(timeout_seconds: int = 40) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            response = httpx.get(f"{APP_URL}/api/system/health", timeout=1)
            if response.status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    return False


def open_app(icon: pystray.Icon, item=None) -> None:
    webbrowser.open(APP_URL)


def stop_app(icon: pystray.Icon, item=None) -> None:
    icon.stop()
    if server is not None:
        server.should_exit = True


def main() -> None:
    threading.Thread(target=run_server, daemon=True).start()

    image = load_tray_icon()
    menu = pystray.Menu(
        pystray.MenuItem("TickeTess - Online", None, enabled=False),
        pystray.MenuItem("Abrir TickeTess", open_app, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Encerrar servidor", stop_app),
    )
    icon = pystray.Icon("ticketess", image, "TickeTess - Online", menu)

    def open_when_ready() -> None:
        if wait_until_ready():
            webbrowser.open(APP_URL)

    threading.Thread(target=open_when_ready, daemon=True).start()

    icon.run()


if __name__ == "__main__":
    main()
