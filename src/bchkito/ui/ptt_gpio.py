from __future__ import annotations

import logging
import sys
import threading
from typing import Callable

from bchkito.config import Settings

logger = logging.getLogger(__name__)


class PushToTalk:
    """Push-to-talk: keyboard (space) on desktop, GPIO button on Pi."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._pressed = False
        self._stop = threading.Event()
        self._mode = settings.ptt_mode

    def start(self) -> None:
        if self._mode == "auto":
            self._mode = "gpio" if self._gpio_available() else "keyboard"
        if self._mode == "gpio":
            self._start_gpio()
        else:
            self._start_keyboard()

    def stop(self) -> None:
        self._stop.set()

    def is_pressed(self) -> bool:
        return self._pressed

    def wait_press(self) -> None:
        while not self._stop.is_set() and not self._pressed:
            self._stop.wait(0.05)

    def wait_release(self) -> None:
        while not self._stop.is_set() and self._pressed:
            self._stop.wait(0.05)

    def _gpio_available(self) -> bool:
        try:
            import gpiozero  # noqa: F401

            return True
        except Exception:
            return False

    def _start_gpio(self) -> None:
        try:
            from gpiozero import Button
        except Exception as exc:  # pragma: no cover
            logger.warning("GPIO unavailable (%s); falling back to keyboard", exc)
            self._mode = "keyboard"
            self._start_keyboard()
            return

        button = Button(self.settings.ptt_gpio_pin, pull_up=True)
        button.when_pressed = lambda: setattr(self, "_pressed", True)
        button.when_released = lambda: setattr(self, "_pressed", False)
        logger.info("PTT GPIO on pin %s", self.settings.ptt_gpio_pin)
        self._button = button

    def _start_keyboard(self) -> None:
        logger.info("PTT keyboard mode: hold SPACE to talk, ENTER for text demo, Ctrl+C to quit")

        def reader() -> None:
            try:
                import msvcrt  # type: ignore

                while not self._stop.is_set():
                    if msvcrt.kbhit():
                        ch = msvcrt.getch()
                        if ch in (b" ",):
                            self._pressed = True
                            # hold until space released is hard on Windows console;
                            # treat next key as release if space again or timeout via loop
                        elif ch in (b"\r", b"\n"):
                            self._pressed = False
                        elif ch in (b"\x03",):
                            self._stop.set()
                    else:
                        self._stop.wait(0.05)
            except ImportError:
                # POSIX tty
                import select
                import termios
                import tty

                fd = sys.stdin.fileno()
                old = termios.tcgetattr(fd)
                try:
                    tty.setcbreak(fd)
                    while not self._stop.is_set():
                        r, _, _ = select.select([sys.stdin], [], [], 0.05)
                        if r:
                            ch = sys.stdin.read(1)
                            if ch == " ":
                                self._pressed = not self._pressed
                            elif ch in {"\n", "\r"}:
                                self._pressed = False
                            elif ch == "\x03":
                                self._stop.set()
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old)

        threading.Thread(target=reader, daemon=True).start()


def make_ptt_predicate(ptt: PushToTalk) -> Callable[[], bool]:
    return ptt.is_pressed
