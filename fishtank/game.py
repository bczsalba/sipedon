"""
fishtank.game
-------------
author: bczsalba


This module provides all the game logic for the module.
It is essentially an implementation of the classes defined in 
`classes`, so if you want to create your own application using
the names defined there this module can be ignored.
"""

from __future__ import annotations

import pytermgui as ptg

from .windows import AquariumWindow
from .classes import Fish, Aquarium


class Game(ptg.WindowManager):
    """
    The class that handles all game logic.

    Start a game by initiating it, and calling its `start` method.
    """

    # How many points a player is awarded per second per fish
    payrate = 1

    def __init__(self) -> None:
        """Initialize object"""

        super().__init__()

        self._aquarium_index = 0
        self._aquariums: list[AquariumWindow] = []

        # self.view =

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Game:
        """Get game from saved JSON object"""

    @property
    def current(self) -> Aquarium:
        """Return currently selected AquariumContainer"""

        return self._aquariums[self._aquarium_index]

    def add_aquarium(self) -> AquariumContainer:
        """Add a new AquariumContainer object, return it"""

        new = AquariumContainer(self.framerate)
        self._aquariums.append(new)

        return new

    def start(self) -> None:
        """Start game execution"""


def main() -> None:
    """Main method"""

    with ptg.WindowManager() as manager:
        view = AquariumWindow(
            manager.framerate, width=65, height=30, pos=(10, 10)
        ).center()
        view += Fish()
        view += Fish()
        view += Fish()
        view += Fish()

        # tank = AquariumWindow(manager.framerate, width=65, height=30)

        manager.add(view)
        manager.run()


if __name__ == "__main__":
    main()
