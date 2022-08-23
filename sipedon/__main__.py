import time
import random

from pytermgui import terminal, clear, alt_buffer, tim
from pytermgui.input import getch_timeout, keys

from .classes import Position, Aquarium, Fish, Food


def center_x(text: str) -> None:
    return (terminal.width - len(text)) // 2


def main() -> None:
    extra_buffer: list[tuple[float, str]] = []

    def display_for(timeout: float, text: str) -> None:
        extra_buffer.append((timeout, text))

    aquarium = Aquarium(Position(1, 1), terminal.width, terminal.height)

    for _ in range(20):
        x = random.randint(terminal.origin[0], terminal.width)
        y = random.randint(terminal.origin[1], terminal.height)

        aquarium += Fish(pos=Position(x, y))

    paused = False
    frametime = 1 / 20

    with alt_buffer(cursor=False, echo=False):
        aquarium.show()
        # time.sleep(0.5)

        while True:
            if not paused:
                aquarium.update()

            clear()

            with terminal.record() as recording:
                aquarium.print(flush=False)

                for i, (timeout, text) in enumerate(extra_buffer.copy()):
                    if timeout < 0.0:
                        extra_buffer.pop(i)
                        continue

                    terminal.write(text)
                    extra_buffer[i] = timeout - frametime, text

            key = getch_timeout(frametime, interrupts=False)

            if key == chr(3):
                break

            if key == "*":
                recording.save_svg("screenshot.svg", title="Sipedon")
                message = "Screenshot saved!"

                display_for(
                    0.7,
                    tim.parse(
                        "[({};{}) bold primary]{}".format(
                            terminal.height, center_x(message), message
                        )
                    ),
                )

            if key == " ":
                paused = not paused

            if key == keys.ENTER:
                margin = terminal.width // 5
                area = range(margin, terminal.width - margin)

                for x in area:
                    aquarium += Food(pos=Position(x, 3))

    print()
    fish = random.choice(aquarium.fish)
    tim.print(f"[slategrey italic]~~ [/]Goodbye {fish.skin} [slategrey italic]~~")
