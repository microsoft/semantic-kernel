#! /usr/bin/env python

"""Script that gets run by rcc right before the robot starts.
(consult robot.yaml in order to see how this is called and with what parameters)

This illustrates the fact that you can do certain pre-run actions which will prepare
the bot for the actual run. This example script just writes some random text into a
file we decide later on to attach into the generated Producer's output Work Items.
"""


import sys
import time
from pathlib import Path


def main(argc, argv):
    """Main entry point of the script which gets executed before the bot starts."""
    # Use `argparse` for better support towards CLI argument parsing:
    #  https://docs.python.org/3/library/argparse.html
    if argc != 2:
        print(f"Usage: {argv[0]} PATH")
        return 1  # invalid usage

    # Write in the passed path some random text content.
    path = Path(argv[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    current_time = time.ctime()
    path.write_text(f"This is just a text file. (generated at {current_time})\n")

    return 0  # run fine


if __name__ == "__main__":
    # Call the main function with CLI arguments and exit with a return code. A non-zero
    #  value will interrupt the bot execution.
    return_code = main(len(sys.argv), sys.argv)  # called with CLI arguments
    sys.exit(int(return_code or 0))  # exits with above return code
