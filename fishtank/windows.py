"""
fishtank.windows
------------------
author: bczsalba


This module provides the pytermgui `Window` classes that
implement the `Aquarium` system.
"""

from __future__ import annotations

from typing import Any, Type

import pytermgui as ptg

from .classes import AquariumChild, Aquarium, Fish, Position, Food

box = ptg.boxes.Box(
    [
        "===========",
        "||>| x ||<|",
        "===========",
    ]
)


class AquariumWindow(ptg.Window):  # pylint: disable=too-many-instance-attributes
    """Window that contains an Aquarium"""

    is_noresize = True
    is_noblur = True

    simulation_framerate = 20

    def __init__(self, manager_framerate: int = 60, **attrs) -> None:
        """Initialize object"""

        super().__init__(**attrs)

        self.box = box

        self.aquarium = Aquarium(
            self._get_position(),
            width=self.width - self.sidelength,
            height=self.height,
        )

        self.set_framerate(manager_framerate)
        self._last_size = (self.width, self.height)
        self._last_pos = self.pos

        self._framecount = 0
        self._is_feeding = False

        self.is_dirty = True

    def __iadd__(self, other: object) -> AquariumWindow:
        """Add `Fish` object to inner `Aquarium`"""

        if not isinstance(other, Fish):
            raise TypeError(f"You can only add `Fish` to `{type(self)}` object")

        self.aquarium += other
        return self

    def _should_draw(self) -> bool:
        """Determine if enough frames have elapsed since last `update()`"""

        return self._framecount % self._drawn_frame_index == 0

    def _get_position(self) -> Position:
        """Get a position that incorporates `sidelength`"""

        xpos, ypos = self.pos
        return Position(xpos + self.sidelength // 2, ypos + 1)

    def set_framerate(self, new: int) -> None:
        """Set new framerate to adjust simulation framerate to"""

        self.framerate = 120 - new
        self._drawn_frame_index = max(int(new / self.simulation_framerate), 1)

    def handle_mouse(
        self, event: ptg.MouseEvent, target: ptg.widgets.base.MouseTarget | None = None
    ) -> bool:
        """Drop food if clicked"""

        action, pos = event

        if not self.pos[0] < pos[0] < self.pos[0] + self.width - 1:
            return False

        if not self.pos[1] < pos[1] < self.pos[1] + self.height + 1:
            return False

        if action is ptg.MouseAction.LEFT_CLICK:
            self._is_feeding = True

        elif action is ptg.MouseAction.RELEASE:
            self._is_feeding = False

        position = Position.from_tuple(pos)
        if self._is_feeding and self.aquarium.get_type_at(Food, position) is None:
            self.aquarium += Food(position)

        return False

    def get_lines(self) -> list[str]:
        """Get current lines of `self.aquarium`"""

        old = self.height
        if self.pos != self._last_pos:
            self.aquarium.move(self._get_position())

        if self._should_draw():
            self._last_pos = self.pos
            self.aquarium.update()

        self._framecount += 1
        lines = super().get_lines() + [str(self.aquarium)]

        self.height = old

        return lines


class AquariumDebugger(ptg.Window):
    """A window that serves to debug information on an aquarium"""

    is_noblur = True
    is_noresize = True

    def __init__(self, aquarium_win: AquariumWindow) -> None:
        """Initialize object"""

        self._target = aquarium_win
        super().__init__(width=34)

        self.is_dirty = True

    def get_lines(self) -> list[str]:
        """Build `Window` contents and `get_lines()`"""

        def _get_auto(data: Any) -> ptg.widgets.base.Widget:
            """Get `auto` widget from `data`"""

            widget = ptg.auto(data)
            assert isinstance(widget, ptg.Widget)
            return widget

        self._widgets = []

        self._widgets.append(_get_auto("[210 bold]Debug Info"))
        self._widgets.append(_get_auto(""))

        types: dict[Type[AquariumChild], int] = {}
        for child in self._target.aquarium.children:
            if type(child) not in types:
                types[type(child)] = 0
                continue

            types[type(child)] += 1

        for child_type, count in types.items():
            name = child_type.__name__
            self._widgets.append(_get_auto(f"[68]{name:<20}[/fg]: [157]{count:>5}"))

        if self.manager is not None:
            self._widgets.append(_get_auto(""))
            self._widgets.append(
                _get_auto(f"{'Manager framerate':<20}: {str(self.manager.fps):>5}")
            )

        targeted = sorted(
            [food for food in self._target.aquarium.food], key=lambda f: f.targeters
        )
        # if len(targeted) > 0:
        #     largest_targeted = targeted[-1]

        #     self._widgets.append(ptg.Label("Most wanted:"))
        #     self._widgets.append(ptg.Label(f"{largest_targeted.targeters}"))

        return super().get_lines()
