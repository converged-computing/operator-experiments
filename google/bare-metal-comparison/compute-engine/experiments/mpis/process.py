#!/usr/bin/env python3

import os
import argparse
import json
import re
import sys
import pandas
import seaborn as sns
import matplotlib.pyplot as plt


def recursive_find(base, pattern="^(mpis[.]log|mpis.*[.]log|mpis[.]log)$"):
    """
    Recursively find lammps output files.
    """
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            if re.search(pattern, filename):
                yield os.path.join(root, filename)


def read_file(filename):
    """
    Read a file into a text blob.
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def read_json(filename):
    """
    Read a json file into a dict.
    """
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content


def read_lines(filename):
    """
    Read lines of a file into a list.
    """
    with open(filename, "r") as fd:
        lines = fd.readlines()
    return lines


def get_first_int(match):
    return int(match.group().strip().split(" ")[0])


def timestr2seconds(timestr):
    """
    Given a timestring in two formats, return seconds (float).
    """
    # Minutes and seconds, MM:SS.mm
    if timestr.count(":") == 1:
        minutes, seconds = timestr.split(":")
        return (int(minutes) * 60) + float(seconds)

    # hours, minutes, seconds HH:MM:SS.mm
    elif timestr.count(":") == 2:
        hours, minutes, seconds = timestr.split(":")
        return (int(hours) * 360) + (int(minutes) * 60) + float(seconds)
    raise ValueError(f"Unrecognized time format {timestr}")


def gather_outputs(outdir):
    # Store results by machine / size
    results = {}

    # Handle partial / relative / "." paths
    outdir = os.path.abspath(outdir)
    if not os.path.exists(outdir):
        sys.exit(f"{outdir} does not exist.")

    # Here we only have MPI runs with different times so we don't care about output!
    for file in recursive_find(outdir):
        lines = read_lines(file)

        entry = {}

        # Get the associated flux output json file
        # I didn't get logs for all of the lammps runs - didn't need them
        flux_log = "%s-info.json" % file.rstrip(".log")
        if os.path.exists(flux_log):
            entry["fluxinfo"] = read_json(flux_log)
            results[file] = entry

    return {"results": results}


def get_parser():
    """
    Return process laamps output parser.

    We require an output directory, optionally a plot name and slot/pod boolean.
    """
    parser = argparse.ArgumentParser(description="Process LAMMPS outputs")
    parser.add_argument("data_dir", help="data directory root")
    parser.add_argument("--meta", help="meta.json for experiments.")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    results = gather_outputs(args.data_dir)

    # Save temporary results for viewing / run plot_results.py results.json
    with open("results.json", "w") as fd:
        fd.write(json.dumps(results, indent=4))


if __name__ == "__main__":
    main()
