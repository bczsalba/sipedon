"""
fishtank.__main__
------------------
author: bczsalba


This module provides the runtime of the library.
See `fishtank -h` for more information.
"""

from __future__ import annotations

import pytermgui as ptg

from .classes import Aquarium, Fish
from .windows import AquariumWindow, AquariumDebugger


class BottomDweller(Fish):
    """A fish who lives at the bottom of the tank"""

    lower_bound = 0.7
    upper_bound = 1.0

    movelimits = [10, 1]
    skin = r"\='\\"

    pigment_pool = [33, 79, 105]


class MidDweller(Fish):
    """A fish who lives at the middle of the tank"""

    lower_bound = 0.3
    upper_bound = 0.75

    pigment_pool = [34, 70, 106]


class TopDweller(Fish):
    """A fish who lives at the top of the tank"""

    lower_bound = 0.0
    upper_bound = 0.35
    skin = r">-"

    pigment_pool = [210, 174, 138]


def clear_food(aquarium: Aquarium) -> None:
    """Remove all food from aquarium"""

    for food in aquarium.food:
        aquarium.children.remove(food)


def main() -> None:
    """Main function"""

    # TODO: Do arguments & shiz
    # process_arguments()

    with ptg.WindowManager() as manager:
        manager.framerate = 120
        awi = AquariumWindow(manager_framerate=manager.framerate, width=65, height=30)
        awi.center()
        for _ in range(5):
            awi += TopDweller()
            awi += MidDweller()
            awi += BottomDweller()

        awi.get_lines()

        manager.add(awi)
        # manager.add(AquariumDebugger(awi))

        manager.bind("*", lambda *_: manager.show_targets())
        manager.bind("R", lambda *_: clear_food(awi.aquarium))

        manager.run()


if __name__ == "__main__":
    main()
