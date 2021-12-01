"""
fishtank.classes
----------------
author: bczsalba


This module is the entry point for console scripts.

In the future it will run game:main(), but for now
it calls __init__:main().
"""

from . import main as _main


def main() -> None:
    """Call main runtime method"""

    _main()


if __name__ == "__main__":
    main()
