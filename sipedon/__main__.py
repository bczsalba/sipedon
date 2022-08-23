import time
from pytermgui import terminal, clear, alt_buffer, tim
from pytermgui.input import getch_timeout, keys

from .classes import Position, Aquarium, Fish


def main() -> None:
    aquarium = Aquarium(Position(1, 1), terminal.width, terminal.height)

    for _ in range(10):
        aquarium += Fish()

    paused = False
    with alt_buffer(cursor=False, echo=False):
        while True:
            if not paused:
                aquarium.update()

            clear()

            with terminal.record() as recording:
                terminal.print(aquarium)

            key = getch_timeout(1 / 20, interrupts=False)

            if key == chr(3):
                break

            if key == "*":
                recording.save_svg("screenshot.svg", title="Sipedon")

            if key == " ":
                paused = not paused

    print()
    tim.print("[slategrey italic]~~ [/]Goodbye ><'> [slategrey italic]~~")
