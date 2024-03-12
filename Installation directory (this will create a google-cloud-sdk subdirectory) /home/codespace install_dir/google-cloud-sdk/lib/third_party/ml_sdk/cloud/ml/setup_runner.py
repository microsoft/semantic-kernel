"""A py_binary running that's equivalent to running "python setup.py"."""

import sys
import setuptools

del setuptools  # Ensure setuptools is available.


def main():
  if len(sys.argv) <= 1:
    raise RuntimeError("Must specify setup.py file as the first argument.")

  with open(sys.argv[1], "r") as f:
    setup_content = f.read()
  # Simulates running "python setup.py" by removing the setup_runner from
  # sys.argv[0].
  sys.argv = sys.argv[1:]
  exec(setup_content)  # pylint: disable=exec-used


if __name__ == "__main__":
  main()
