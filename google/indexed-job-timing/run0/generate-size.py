#!/usr/bin/env python3

# Launch jobs and watch for pods events. We only care about the ids and when they are created
# and then we can compare between cases. Since we have a small testing cluster here (kind)
# we will only do small tests.
import argparse
import os
import re
import sys

# Save data here
here = os.path.dirname(os.path.abspath(__file__))
templates = os.path.join(here, "templates")
experiments = os.path.join(here, "experiments")


def recursive_find(base, pattern=None):
    """
    Find filenames that match a particular pattern, and yield them.
    """
    # We can identify modules by finding module.lua
    for root, folders, files in os.walk(base):
        for file in files:
            fullpath = os.path.abspath(os.path.join(root, file))

            if pattern and not re.search(pattern, fullpath):
                continue
            yield fullpath


def read_file(path):
    with open(path, "r") as fd:
        content = fd.read()
    return content


def write_file(content, path):
    with open(path, "w") as fd:
        fd.write(content)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Pod Experiment Generator",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("size", help="Size to generate", type=int)
    return parser


def main():
    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, _ = parser.parse_known_args()

    if not args.size:
        sys.exit("Please provide the data size as the only argument")
    print(f"Generating experiments for size {args.size}")

    outdir = os.path.join(experiments, f"size-{args.size}")
    if os.path.exists(outdir):
        sys.exit(f"Experiment directory {outdir} has already been created.")
    os.makedirs(outdir)

    # Experiment input files
    files = list(recursive_find(templates, "[.](yml|yaml)$"))

    # This is a bit manual, OK for now
    for filename in files:
        content = read_file(filename)

        # I call this "janky jinja"
        content = content.replace("[[size]]", str(args.size))
        if "pods" in os.path.basename(filename):
            result = ""
            for idx in range(0, args.size):
                result += content.replace("[[index]]", str(idx))
                if idx != args.size - 1:
                    result += "---\n"
            content = result.strip()

        # Save output file
        outfile = os.path.join(outdir, os.path.basename(filename))
        write_file(content, outfile)


if __name__ == "__main__":
    main()
