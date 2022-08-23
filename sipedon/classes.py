"""
This module contains the active classes this module defines.
These are all meant to be agnostic to the system running them,
and are controlled in a leveled manner. This means that a
Position has no idea what it belongs to, and a Fish has no way
of accessing the aquarium.

This is like this so you can swap out each part and not have to
tangle around in the source.
"""

from __future__ import annotations

import sys
import math
import random
from dataclasses import dataclass
from typing import Iterator, Type

from abc import ABC, abstractmethod

from pytermgui import tim, terminal, real_length

# A string that sets the cursor position
# Format: \x1b[{y};{x}H{content}
PositionedStr = str


@dataclass
class Position:
    """Object that represents an `x,y` position"""

    xcoord: int
    ycoord: int

    @classmethod
    def from_tuple(cls, data: tuple[int, int]) -> Position:
        """Creates a Position from a tuple.

        Args:
            data: A tuple of 2 ints, used as `xcoord, ycoord`.

        Returns:
            The Position that corresponds to the input.
        """

        return cls(data[0], data[1])

    @classmethod
    def origin(cls) -> Position:
        """Returns the terminal's origin, as a position."""

        return Position.from_tuple(terminal.origin)

    def __add__(self, other: object) -> Position:
        """Sums two positions.

        Args:
            other: The object to add.

        Returns:
            A **new** Position instance, that is generated as the 'result' of `self + other`.

        Raises:
            TypeError: Non-position object given as `other`.
        """

        if not isinstance(other, Position):
            raise TypeError(f"You can only add {type(self)} to {type(self)} objects.")

        s_x, s_y = self
        o_x, o_y = other

        return Position(s_x + o_x, s_y + o_y)

    def __sub__(self, other: object) -> Position:
        """Subtracts two positions.

        Args:
            other: The object to subtract from self.

        Returns:
            A **new** Position instance, that is generated as the 'result' of `self - other`.

        Raises:
            TypeError: Non-position object given as `other`.
        """

        if not isinstance(other, Position):
            raise TypeError(f"You can only add {type(self)} to {type(self)} objects.")

        s_x, s_y = self
        o_x, o_y = other

        return Position(s_x - o_x, s_y - o_y)

    def __iter__(self) -> Iterator[int]:
        """Iterates through coordinates."""

        return iter((self.xcoord, self.ycoord))

    def distance_to(self, other: Position) -> float:
        """Calculates the distance between two positions.

        Args:
            other: The Position to compare to.

        Returns:
            The (always positive) distance between self and other.
        """

        return abs(
            math.sqrt(
                (other.xcoord - self.xcoord) ** 2 + (other.ycoord - self.ycoord) ** 2
            )
        )

    def to_ansi(self) -> str:
        """Returns an ANSI positioner string."""

        return f"\x1b[{self.ycoord};{self.xcoord}H"

    def __call__(self, text: str) -> str:
        r"""Positions to given string using ANSI sequences.

        Args:
            text: The string to prepend the positioner to.

        Returns:
            A string, that when printed on an xterm terminal, will be located at the
                position that self describes. This will follow the format:

                    \x1b[{self.ycoord};{self.xcoord}H{text}
        """

        return self.to_ansi() + text


class AquariumChild(ABC):
    """Base class for all children of an aquarium."""

    def __init__(self, pos: Position = Position.origin()) -> None:
        """Initialize object"""

        self.lifetime = 0
        self.pos = pos

    def move_origin(self, diff: Position) -> None:
        """Moves all stored positions of this child by some amount.

        Args:
            diff: The Position that should be summed onto every position.
        """

        self.pos += diff

    @abstractmethod
    def update(self, aquarium: Aquarium) -> bool:
        """Updates state, including position.

        Args:
            aquarium: The parent Aquarium object.

        Returns:
            True in the event of a successful update, False otherwise.
        """

    @property
    @abstractmethod
    def width(self) -> int:
        """Returns the width of this child."""


class Food(AquariumChild):
    """A single food particle."""

    char: str = "#"
    pigment_pool: list[int] = [255, 250, 241]

    def __init__(self, pos: Position = Position.origin()) -> None:
        super().__init__(pos)

        self.pos = pos
        color = random.choice(self.pigment_pool)
        self.skin = tim.parse(f"[{color}]{self.char}")
        self.endpoint: int | None = None

        self.is_static: bool = False
        self.targeters = 0
        self._previous_horizontal = 0

    @property
    def width(self) -> int:
        """Gets the width of this particle."""

        return len(self.char)

    def _get_x(self) -> int:
        """Gets the next x movement direction, based on our previous move."""

        if self._previous_horizontal == 0:
            return random.randint(-1, 1)

        return 0

    def update(self, aquarium: Aquarium) -> bool:
        """Updates the position & path of this particle."""

        color = max(237, int(255 - self.lifetime / 3))
        self.skin = tim.parse(f"[{color}]{self.char}")

        if self.endpoint is None:
            return False

        if self.pos.ycoord >= self.endpoint or self.is_static:
            self.is_static = True
            return True

        horizontal = self._get_x()
        new = self.pos + Position(horizontal, random.choice([0, 0, 1]))

        competition = aquarium.get_type_at(Food, new)
        if competition is not None and competition.is_static:
            self.is_static = True
            return True

        self.pos = new
        self._previous_horizontal = horizontal

        return True


class Fish(AquariumChild):  # pylint: disable=too-many-instance-attributes
    """A fish in an aquarium."""

    lower_bound = 0.0
    upper_bound = 1.0

    movelimits = [-1, -1]
    base_skin = "><'>"

    pigment_pool: list[int] = [243, 226, 220, 255]
    pigment_length: int = len(base_skin)

    def __init__(
        self,
        skin: str | None = None,
        pigment: list[int] | None = None,
        pos: Position = Position.origin(),
    ) -> None:
        super().__init__(pos)

        self.heading = 1
        self.target: Food | None = None

        self._skip_frame = False
        self._path: list[tuple[Position, int]] = []

        if pigment is None:
            pigment = self._get_pigment()

        self.pigment = pigment
        self.skin = skin or self.base_skin

    @property
    def width(self) -> int:
        """Gets the width of this fish."""

        return real_length(self.skin)

    @property
    def skin(self) -> str:
        """Returns the currently applied (facing & pigmented) skin."""

        return self.skins[self.heading]

    @skin.setter
    def skin(self, new: str) -> None:
        """Sets the new skin, applies pigmentations & does the same for the reverse."""

        def _apply_pigment(skin) -> str:
            """Apply pigment to a skin"""

            buff = ""
            for i, char in enumerate(skin):
                if char == "\\":
                    char += "\\"

                i = min(i, len(self.pigment) - 1)
                buff += f"[{self.pigment[i]}]{char}"

            return tim.parse(buff)

        self._skin = new

        self.skins: dict[int, str] = {
            -1: _apply_pigment(self._reverse_skin(new)),
            1: _apply_pigment(new),
        }

        # TODO: Support multiple lines
        self.height = len(new.splitlines())

    @staticmethod
    def _reverse_skin(skin: str) -> str:
        """Returns the given skin, reversed using character pairs.

        Args:
            skin: The skin to reverse.

        Returns:
            A string, that is the result of:

                - Reversing `skin`
                - Flipping all characters with symmetrical pairs

            For example, the skin `><'>` would become `<'><` when reversed.
        """

        reversed_skin = ""
        reversible = ["<>", "[]", "{}", "()", "/\\", "db", "qp"]
        for char in reversed(skin):
            for rev in reversible:
                if char in rev:
                    new = rev[rev.index(char) - 1]
                    break
            else:
                new = char

            reversed_skin += new

        return reversed_skin

    def _get_pigment(self) -> list[int]:
        """Gets a list of pigmentations to use by chosing from the pigment pool."""

        pigment = []
        for _ in range(self.pigment_length):
            pigment.append(random.choice(self.pigment_pool))

        return pigment

    def update(self, aquarium: Aquarium) -> bool:
        """Updates the position & path of this fish."""

        if self.target is None and aquarium.has_type(Food):
            for food in aquarium.food:
                if food.targeters < 2 and self.pos.distance_to(food.pos) <= 5:
                    self.target = food
                    food.targeters += 1
                    self.update_path(food.pos)
                    break

        if self.target is not None:
            if self.pos.distance_to(self.target.pos) <= 1:
                self.target.targeters -= 1
                if self.target in aquarium.children:
                    aquarium.children.remove(self.target)

                self.target = None
                return False

            self.update_path(self.target.pos)

            # Do an extra update to avoid getting stuck
            self.pos, self.heading = self._path.pop(0)

        if len(self._path) == 0:
            rand = random.randint(0, 5)
            heading = self.heading
            if rand < 4:
                for i in range(rand):
                    if i % 3 == 0:
                        heading *= -1

                    self._path.append((self.pos, heading))

                return True

            return False

        if self._skip_frame:
            self._skip_frame = False
            return True

        self.pos, self.heading = self._path.pop(0)
        return True

    def move_origin(self, diff: Position) -> None:
        """Moves fish & its path to new position."""

        super().move_origin(diff)

        for i, (pos, heading) in enumerate(self._path):
            self._path[i] = (pos + diff, heading)

        self._skip_frame = True

    def update_path(self, dest: Position) -> None:  # pylint: disable=too-many-locals
        """Calculates a line to the destination, with a heading for each step.

        This uses Bresenham's line formula for the calculations.

        Args:
            dest: The position to move to.
        """

        startx, starty = self.pos
        endx, endy = dest

        diff = dest - self.pos

        xlimit, ylimit = self.movelimits
        if abs(diff.xcoord) > xlimit > 0:
            sign = 1 if diff.xcoord > 0 else -1
            endx = startx + sign * xlimit

        if ylimit > 0:
            sign = 1 if diff.ycoord > 0 else -1
            endy = starty + sign * ylimit

        # Get x delta, x direction
        diffx = abs(endx - startx)
        intbuff_x = 1 if startx < endx else -1

        # Get y delta, y direction
        diffy = -abs(endy - starty)
        intbuff_y = 1 if starty < endy else -1

        # Set heading
        heading = intbuff_x

        # Calculate error
        error = diffx + diffy

        self._path = []
        while True:
            pos = Position(startx, starty)

            # TODO: Check for position validity
            # if not self._position_valid(pos):
            #     break

            self._path.append((pos, heading))
            if startx == endx and starty == endy:
                break

            error2 = 2 * error

            if error2 >= diffy:
                error += diffy
                startx += intbuff_x

            if error2 <= diffx:
                error += diffx
                starty += intbuff_y


class Aquarium:
    """An container for all of our fish."""

    def __init__(
        self, pos: Position | tuple[int, int], width: int, height: int
    ) -> None:
        """Initializes the aquarium.

        Args:
            pos: The position to use as the top-left corner for the aquarium.
            width: The width of the aquarium.
            height: The height of the aquarium.
        """

        self.pos = pos
        self.width = width
        self.height = height

        self.children: list[AquariumChild] = []

    @property
    def fish(self) -> list[Fish]:
        """Get all `Fish` from `self.children`"""

        return [child for child in self.children if isinstance(child, Fish)]

    @property
    def food(self) -> list[Food]:
        """Get all `Fish` from `self.children`"""

        return [child for child in self.children if isinstance(child, Food)]

    def has_type(self, ttype: Type[AquariumChild]) -> bool:
        """Return whether this aquarium contains contains any of the given type.

        Args:
            ttype: The type to look for.

        Returns:
            True if any of the given type is a child of this aquarium.
        """

        return any(isinstance(child, ttype) for child in self.children)

    def __iadd__(self, other: object) -> Aquarium:
        """Calls `add` with the given object."""

        if not isinstance(other, AquariumChild):
            raise TypeError(
                f"You can only add `AquariumChild`-s to `{type(self)}` objects"
            )

        self.add(other)

        return self

    def _get_destination(self, fish: Fish) -> Position:
        """Gets new destination for the given child."""

        pos = Position(
            self.pos.xcoord + random.randint(-1, self.width - fish.width),
            self.pos.ycoord
            + random.randint(
                1 + int(self.height * fish.lower_bound),
                1 + int(self.height * fish.upper_bound),
            ),
        )

        return pos

    def clamp(self, child: AquariumChild) -> None:
        """Clamps a child's coordinates within the aquarium.

        Args:
            child: The child to clamp.
        """

        child.pos.xcoord = max(
            min(self.pos.xcoord + self.width - child.width + 1, child.pos.xcoord),
            self.pos.xcoord - 1,
        )

        child.pos.ycoord = max(
            min(self.pos.ycoord + self.height - 1, child.pos.ycoord),
            self.pos.ycoord,
        )

    def add(self, other: AquariumChild, randomize_pos: bool = False) -> None:
        """Sums two positions.

        Args:
            other: The object to add.
            randomize_pos: If set, the given child's position will be randomized within
                the bounds of the aquarium.

        Raises:
            TypeError: Non-AquariumChild object given as `other`.
        """

        if not isinstance(other, AquariumChild):
            raise TypeError(
                f"You can only add object of type AquariumChild to aquariums, not {other!r}."
            )

        self.children.append(other)

        if isinstance(other, Food):
            other.endpoint = self.pos.ycoord + self.height - 1

            for i, fish in enumerate(self.fish):
                if i % 3 == 0:
                    fish.target = other
            return

        if isinstance(other, Fish) and randomize_pos:
            other.pos = self._get_destination(other)

    def get_type_at(
        self, ttype: Type[AquariumChild], pos: Position
    ) -> AquariumChild | None:
        """Tries to find a child at the given position.

        Args:
            ttype: The type of child to look for.
            pos: The position to find the child at.

        Returns:
            The child if one is found, None otherwise.
        """

        for child in self.children:
            if not isinstance(child, ttype):
                continue

            if child.pos == pos:
                return child

        return None

    def move(self, new: Position) -> None:
        """Moves the aquarium to the new position.

        This also affects all children, whos `move_origin` method is called
        with the position difference.
        """

        diff = new - self.pos
        self.pos = new

        for child in self.children:
            child.move_origin(diff)

    def update(self) -> bool:
        """Updates all of our children.

        At the moment, this always returns True.
        """

        for child in self.children:
            if not child.update(self):
                if isinstance(child, Fish):
                    new = self._get_destination(child)
                    child.update_path(new)

                elif isinstance(child, Food):
                    self.children.remove(child)

            self.clamp(child)

            child.lifetime += 1

        return True

    def get_content(self) -> list[tuple[tuple[int, int], str]]:
        """Gets a list of all of our children's position & skin.

        Returns:
            A list of tuples with (child.pos, child.skin).
        """

        content = []
        for child in self.children:
            content.append((child.pos, child.skin))

        return content

    def show(self) -> None:
        """Shows the space occupied by the terminal, using print."""

        buff = ""
        for x in range(0, self.width):
            x += self.pos.xcoord

            for y in range(0, self.height):
                y += self.pos.ycoord

                buff += f"\x1b[{y};{x}H{'#' if x % 2 else 'x'}"

        print(buff, end="", flush=True)

    def print(self, flush: bool = False) -> None:
        """Prints all children.

        Args:
            flush: If set, the terminal's stream will be flushed at the end
                of this routine.
        """

        for pos, skin in self.get_content():
            terminal.write(skin, pos=pos)

        if flush:
            terminal.flush()
