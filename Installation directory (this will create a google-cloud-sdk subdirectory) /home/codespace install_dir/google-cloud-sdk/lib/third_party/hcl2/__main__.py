#!/usr/bin/env python
"""
This script recursively converts hcl2 files to json

Usage:
    hcl2tojson [-s] PATH [OUT_PATH]

Options:
    -s          Skip un-parsable files
    PATH        The path to convert
    OUT_PATH    The path to write files to
    --with-meta If set add meta parameters to the output_json like __start_line__ and __end_line__
"""
import argparse
import json
import os
import sys

from lark import UnexpectedCharacters, UnexpectedToken

from . import load
from .version import __version__


def main():
    """The `console_scripts` entry point"""

    parser = argparse.ArgumentParser(
        description="This script recursively converts hcl2 files to json"
    )
    parser.add_argument(
        "-s", dest="skip", action="store_true", help="Skip un-parsable files"
    )
    parser.add_argument("PATH", help="The file or directory to convert")
    parser.add_argument(
        "OUT_PATH",
        nargs="?",
        help="The path where to write files to. Optional when parsing a single file. "
        "Output is printed to stdout if OUT_PATH is blank",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--with-meta",
        action="store_true",
        help="If set add meta parameters to the output_json like __start_line__ and __end_line__",
    )

    args = parser.parse_args()

    skippable_exceptions = (UnexpectedToken, UnexpectedCharacters, UnicodeDecodeError)

    if os.path.isfile(args.PATH):
        with open(args.PATH, "r", encoding="utf-8") as in_file:
            # pylint: disable=R1732
            out_file = (
                sys.stdout
                if args.OUT_PATH is None
                else open(args.OUT_PATH, "w", encoding="utf-8")
            )
            print(args.PATH, file=sys.stderr, flush=True)
            json.dump(load(in_file, with_meta=args.with_meta), out_file)
            if args.OUT_PATH is None:
                out_file.write("\n")
                out_file.close()
    elif os.path.isdir(args.PATH):
        processed_files = set()
        if args.OUT_PATH is None:
            raise RuntimeError("Positional OUT_PATH parameter shouldn't be empty")
        if not os.path.exists(args.OUT_PATH):
            os.mkdir(args.OUT_PATH)
        for current_dir, _, files in os.walk(args.PATH):
            dir_prefix = os.path.commonpath([args.PATH, current_dir])
            relative_current_dir = os.path.relpath(current_dir, dir_prefix)
            current_out_path = os.path.normpath(
                os.path.join(args.OUT_PATH, relative_current_dir)
            )
            if not os.path.exists(current_out_path):
                os.mkdir(current_out_path)
            for file_name in files:
                in_file_path = os.path.join(current_dir, file_name)
                out_file_path = os.path.join(current_out_path, file_name)
                out_file_path = os.path.splitext(out_file_path)[0] + ".json"

                # skip any files that we already processed or generated to avoid loops and file lock errors
                if in_file_path in processed_files or out_file_path in processed_files:
                    continue

                processed_files.add(in_file_path)
                processed_files.add(out_file_path)

                with open(in_file_path, "r", encoding="utf-8") as in_file:
                    print(in_file_path, file=sys.stderr, flush=True)
                    try:
                        parsed_data = load(in_file)
                    except skippable_exceptions:
                        if args.skip:
                            continue
                        raise
                    with open(out_file_path, "w", encoding="utf-8") as out_file:
                        json.dump(parsed_data, out_file)
    else:
        raise RuntimeError("Invalid Path", args.PATH)


if __name__ == "__main__":
    main()
