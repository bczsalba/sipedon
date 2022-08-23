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

from pytermgui import markup

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
        """Get `Position` instance from a tuple[int, int]"""

        return cls(data[0], data[1])

    def __add__(self, other: object) -> Position:
        """Add `other` to `self`, raise TypeError if other is not `Position`"""

        if not isinstance(other, Position):
            raise TypeError(f"You can only add {type(self)} to {type(self)} objects.")

        s_x, s_y = self
        o_x, o_y = other

        return Position(s_x + o_x, s_y + o_y)

    def __sub__(self, other: object) -> Position:
        """Subtract `other` to `self`, raise TypeError if other is not `Position`"""

        if not isinstance(other, Position):
            raise TypeError(f"You can only add {type(self)} to {type(self)} objects.")

        s_x, s_y = self
        o_x, o_y = other

        return Position(s_x - o_x, s_y - o_y)

    def __iter__(self) -> Iterator[int]:
        """Iterate through coordinates"""

        for pos in [self.xcoord, self.ycoord]:
            yield pos

    def distance_to(self, other: Position) -> float:
        """Calculate the distance to `other`"""

        return abs(
            math.sqrt(
                (other.xcoord - self.xcoord) ** 2 + (other.ycoord - self.ycoord) ** 2
            )
        )

    def to_ansi(self) -> str:
        """Return formatted ANSI string that sets cursor
        position"""

        return f"\x1b[{self.ycoord};{self.xcoord}H"


class AquariumChild(ABC):
    """
    Base class for all children within an aquarium.

    These objects have 3 main methods:
        - `update()`: update child's position, return boolean of success
        - `move_origin(diff: Position)`: update all path elements # TODO: Find a better name
        - `__str__()`: return string containing cursor position setter and the object
    """

    def __init__(self) -> None:
        """Initialize object"""

        self.lifetime = 0

    @abstractmethod
    def update(self, aquarium: Aquarium) -> bool:
        """Update position & state, return boolean of success"""

    @abstractmethod
    def move_origin(self, diff: Position) -> None:
        """This needs a better name"""

    @property
    @abstractmethod
    def width(self) -> int:
        """Get width of object"""

    @abstractmethod
    def __str__(self) -> PositionedStr:
        """Return string containing position setter"""


class Food(AquariumChild):
    """Object that represents a single food particle"""

    char: str = "#"
    pigment_pool: list[int] = [255, 250, 241]

    def __init__(self, pos: Position) -> None:
        """Initialize object"""

        super().__init__()

        self.pos = pos
        color = random.choice(self.pigment_pool)
        self.skin = markup.parse(f"[{color}]{self.char}")
        self.endpoint: int | None = None

        self.is_static: bool = False
        self.targeters = 0
        self._previous_horizontal = 0

    @property
    def width(self) -> int:
        """Get width of Food"""

        return len(self.char)

    def _get_x(self) -> int:
        """Get new x based on previous movement"""

        if self._previous_horizontal == 0:
            return random.randint(-1, 1)

        return 0

    def update(self, aquarium: Aquarium) -> bool:
        """Update Food position"""

        color = max(237, int(255 - self.lifetime / 3))
        self.skin = markup.parse(f"[{color}]{self.char}")

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

    def move_origin(self, diff: Position) -> None:
        """Move Food to new position"""

        self.pos += diff

    def __str__(self) -> PositionedStr:
        """Get positioned string representing the Food"""

        return self.pos.to_ansi() + self.skin


class Fish(AquariumChild):  # pylint: disable=too-many-instance-attributes
    """
    Object that represents a single Fish

    Internally, it follows a path that is defined when
    `Fish.update_path` is called with a new endpoint.

    On each `Fish.swim` call it goes to the next position
    in its path. If it has run out of positions to move to,
    it returns False.
    """

    lower_bound = 0.0
    upper_bound = 1.0

    movelimits = [-1, -1]
    skin = "><'>"

    pigment_pool: list[int] = [243, 226, 220, 255]
    pigment_length: int = len(skin)

    def __init__(self, pigment: list[int] | None = None) -> None:
        """Initialize object"""

        super().__init__()

        self.pos: Position = Position(0, 0)

        self.heading = 1
        self.target: Food | None = None

        self._skip_frame = False
        self._path: list[tuple[Position, int]] = []

        if pigment is None:
            pigment = self._get_pigment()

        self.pigment = pigment
        self.set_skin(self.skin)

    @property
    def width(self) -> int:
        """Get width of Fish"""

        return len(self.base_skin)

    @staticmethod
    def _reverse_skin(skin: str) -> str:
        """Return char by char reversed version of skin"""

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
        """Get pigment list by choosing from `pigment_pool`"""

        pigment = []
        for _ in range(self.pigment_length):
            pigment.append(random.choice(self.pigment_pool))

        return pigment

    def set_skin(self, new: str) -> None:
        """Set skin to `new`, update pigmentation, width & height"""

        def _apply_pigment(skin) -> str:
            """Apply pigment to a skin"""

            buff = ""
            for i, char in enumerate(skin):
                if char == "\\":
                    char += "\\"

                i = min(i, len(self.pigment) - 1)
                buff += f"[{self.pigment[i]}]" + char

            return markup.parse(buff)

        self.base_skin = new

        self.skins: dict[int, str] = {
            -1: _apply_pigment(self._reverse_skin(new)),
            1: _apply_pigment(new),
        }

        # TODO: Support multiple lines
        self.height = len(new.splitlines())

    def update(self, aquarium: Aquarium) -> bool:
        """Update to next `Position` in `_path`"""

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
        """Move fish to new position"""

        self.pos += diff

        for i, (pos, heading) in enumerate(self._path):
            self._path[i] = (pos + diff, heading)

        self._skip_frame = True

    def update_path(self, dest: Position) -> None:  # pylint: disable=too-many-locals
        """Calculate path to `dest`, update `_path`"""

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

    def __str__(self) -> PositionedStr:
        """Return string including position"""

        return self.pos.to_ansi() + self.skins[self.heading]

    def print(self) -> None:
        """Print Fish to its `pos`"""

        print(str(self))


class Aquarium:
    """Object that represents a contianer of all of our Fish"""

    def __init__(self, pos: Position, width: int, height: int) -> None:
        """Initialize object"""

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
        """Return whether `Aquarium` contains an instance of type `ttype`"""

        for child in self.children:
            if isinstance(child, ttype):
                return True

        return False

    def __iadd__(self, other: object) -> Aquarium:
        """Add other to Aquarium, raise `TypeError` if other is not `Fish`"""

        if not isinstance(other, AquariumChild):
            raise TypeError(
                f"You can only add `AquariumChild`-s to `{type(self)}` objects"
            )

        self.add(other)

        return self

    def _get_destination(self, fish: Fish) -> Position:
        """Get new destination"""

        pos = Position(
            self.pos.xcoord + random.randint(-1, self.width - fish.width),
            self.pos.ycoord
            + random.randint(
                1 + int(self.height * fish.lower_bound),
                1 + int(self.height * fish.upper_bound),
            ),
        )

        return pos

    def add(self, other: AquariumChild, keep_pos: bool = False) -> None:
        """Add `AquariumObject` `other` to aquarium"""

        self.children.append(other)

        if isinstance(other, Food):
            other.endpoint = self.pos.ycoord + self.height - 1

            for i, fish in enumerate(self.fish):
                if i % 3 == 0:
                    fish.target = other
            return

        if isinstance(other, Fish) and not keep_pos:
            other.pos = self._get_destination(other)

    def get_type_at(
        self, ttype: Type[AquariumChild], pos: Position
    ) -> AquariumChild | None:
        """Get instance of `ttype` at `pos` if possible, return `None` if none are present"""

        for child in self.children:
            if not isinstance(child, ttype):
                continue

            if child.pos == pos:
                return child

        return None

    def move(self, new: Position) -> None:
        """Move Aquarium & all its fish"""

        diff = new - self.pos
        self.pos = new

        for child in self.children:
            child.move_origin(diff)

    def update(self) -> bool:
        """Update all fish"""

        for child in self.children:
            if not child.update(self):
                if isinstance(child, Fish):
                    new = self._get_destination(child)
                    child.update_path(new)

                elif isinstance(child, Food):
                    self.children.remove(child)

            child.pos.xcoord = max(
                min(self.pos.xcoord + self.width - child.width + 1, child.pos.xcoord),
                self.pos.xcoord - 1,
            )

            child.pos.ycoord = max(
                min(self.pos.ycoord + self.height - 1, child.pos.ycoord),
                self.pos.ycoord,
            )

            child.lifetime += 1

        return True

    def __str__(self) -> str:
        """Get string representing Aquarium"""

        buff = ""

        # Code to visualize the exact area taken up
        # TODO: Make this publically accessible
        # for x in range(0, self.width):
        #     x += self.pos.xcoord

        #     for y in range(0, self.height):
        #         y += self.pos.ycoord

        #         buff += f"\x1b[{y};{x}H#"

        for child in self.children:
            buff += str(child)

        return buff

    def print(self) -> None:
        """Print all fish"""

        sys.stdout.write(str(self))
        sys.stdout.flush()
