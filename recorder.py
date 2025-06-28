from pathlib import Path
import queue
from typing import Optional

from mss import mss
from PIL import Image, ImageDraw
from pynput import mouse
from PyQt5.QtCore import QThread, pyqtSignal

from settings import current_settings

SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

screenshot_count = 0
mouse_listener = None
is_recording = False
click_queue: queue.Queue = queue.Queue()


def clear_click_queue():
    while True:
        try:
            click_queue.get_nowait()
        except queue.Empty:
            break


def capture_click(x: int, y: int, settings: Optional[dict] = None) -> Optional[str]:
    """Capture the screen and highlight the given click position."""
    global screenshot_count
    if settings is None:
        settings = current_settings
    try:
        with mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            radius = settings["highlight_size"] // 2
            color = settings["highlight_color"]

            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            o_draw = ImageDraw.Draw(overlay)
            o_draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=tuple(color),
                outline=tuple(color[:3]) + (255,),
                width=3,
            )
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

            filename = SCREENSHOT_DIR / f"step_{screenshot_count:03d}.png"
            img.save(filename)
            screenshot_count += 1
            return str(filename)
    except Exception as exc:
        print(f"Error capturing screenshot: {exc}")
        return None


def on_click(x, y, button, pressed):
    global is_recording
    if pressed and is_recording and button == mouse.Button.left:
        click_queue.put((x, y))


def wait_for_click():
    return click_queue.get()


def start_recording():
    global mouse_listener, is_recording, screenshot_count
    clear_click_queue()
    for f in SCREENSHOT_DIR.glob("*.png"):
        try:
            f.unlink()
        except Exception as exc:
            print(f"Warning: could not remove {f}: {exc}")
    screenshot_count = 0
    is_recording = True
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()
    print("[*] Recording started. Click around to capture steps!")


def stop_recording():
    global mouse_listener, is_recording
    is_recording = False
    if mouse_listener:
        mouse_listener.stop()
        mouse_listener = None
        print("[*] Recording stopped.")
    clear_click_queue()


class CaptureThread(QThread):
    screenshot_taken = pyqtSignal(str)

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._running = True

    def run(self):
        while self._running:
            x, y = wait_for_click()
            if x is None and y is None:
                break
            filename = capture_click(x, y, self.settings)
            if filename:
                self.screenshot_taken.emit(filename)

    def stop(self):
        self._running = False
        click_queue.put((None, None))
        self.wait()
