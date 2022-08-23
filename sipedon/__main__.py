import time
from pytermgui import terminal, clear, alt_buffer

from .classes import Position, Aquarium, Fish


def main() -> None:
    aquarium = Aquarium(Position(1, 1), terminal.width, terminal.height)

    for _ in range(10):
        aquarium += Fish()

    with alt_buffer(cursor=False, echo=False):
        while True:
            aquarium.update()

            clear()
            print(aquarium)

            time.sleep(1 / 20)
