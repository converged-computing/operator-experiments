#!/usr/bin/env python3

import argparse
import collections
import fnmatch
import json
import os
import re

import matplotlib.pyplot as plt
import metricsoperator.utils as utils
import pandas
import seaborn as sns

plt.style.use("bmh")
here = os.path.dirname(os.path.abspath(__file__))


def get_parser():
    parser = argparse.ArgumentParser(
        description="Plot LAMMPS Raw Files",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--results",
        help="directory with raw results data",
        default=os.path.join(here, "results", "batch-2"),
    )
    parser.add_argument(
        "--out",
        help="directory to save parsed results",
        default=os.path.join(here, "img"),
    )
    return parser


def recursive_find(base, pattern="*.*"):
    """
    Recursively find and yield files matching a glob pattern.
    """
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def find_inputs(input_dir):
    """
    Find inputs (results files)
    """
    files = []
    for filename in recursive_find(input_dir, pattern="*.log"):
        # We only have data for small
        files.append(filename)
    return files


def main():
    """
    Run the main plotting operation!
    """
    parser = get_parser()
    args, _ = parser.parse_known_args()

    # Output images and data
    outdir = os.path.abspath(args.out)
    indir = os.path.abspath(args.results)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Find input files (skip anything with test)
    files = find_inputs(indir)
    if not files:
        raise ValueError(f"There are no input files in {indir}")

    # This does the actual parsing of data into a formatted variant
    # Has keys results, iters, and columns
    df = parse_data(files)
    df.to_csv(os.path.join(outdir, "lammps-times.csv"))
    plot_results(df, outdir)

    # Show means grouped by experiment to sanity check plots
    print(df.groupby(["scheduler", "experiment"]).total_time.mean())
    print(df.groupby(["scheduler", "experiment"]).total_time.std())


def plot_results(df, outdir):
    """
    Plot lammps results
    """
    # Plot each!
    colors = sns.color_palette("hls", 16)
    hexcolors = colors.as_hex()
    types = list(df.scheduler.unique())
    types.sort()

    # ALWAYS double check this ordering, this
    # is almost always wrong and the colors are messed up
    palette = collections.OrderedDict()
    for t in types:
        palette[t] = hexcolors.pop(0)

    make_plot(
        df,
        title="LAMMPS Wall Times Across Experiments Between Fluence and the Default Scheduler",
        tag="lammps-wall-times",
        ydimension="wall_time",
        xdimension="experiment",
        palette=palette,
        outdir=outdir,
        ext="png",
        plotname="lammps-wall-times",
        hue="scheduler",
        plot_type="bar",
        xlabel="Experiment",
        ylabel="Time (seconds)",
    )

    make_plot(
        df,
        title="LAMMPS Total Time Across Experiments Between Fluence and the Default Scheduler",
        tag="lammps-total-times",
        ydimension="total_time",
        xdimension="experiment",
        palette=palette,
        outdir=outdir,
        ext="png",
        plotname="lammps-total-times",
        hue="scheduler",
        plot_type="bar",
        xlabel="Experiment",
        ylabel="Time (seconds)",
    )


def get_scheduler(filename):
    if "original" in filename:
        return "fluence-original"
    if "fluence" in filename:
        return "fluence"
    return "default"


def parse_data(files):
    """
    Given a listing of files, parse into results data frame
    """
    # Parse into data frame
    df = pandas.DataFrame(
        columns=[
            "ranks",
            "size",
            "x",
            "y",
            "z",
            "experiment",
            "scheduler",
            "wall_time",
            "total_time",
        ]
    )
    idx = 0

    for filename in files:
        # Skip events files
        if "events.log" in filename:
            continue
        scheduler = get_scheduler(filename)
        parsed = os.path.relpath(filename, here)

        # This can be split into pieces by ===
        item = utils.read_file(filename)
        pieces = [x.strip() for x in item.split("===") if x.strip()]

        # parse experiment info from the filename
        base = os.path.basename(filename).replace(".log", "")
        match = re.search(
            "(?P<batch>batch-.*)-(?P<iter>iter-.*)-size-(?P<size>.*)", base
        )
        groups = match.groupdict()
        size, x, y, z = groups["size"].split("-")

        # Find the lammps log
        log = [x for x in pieces if "Total wall time" in x]

        # This is the LAMMPS section with wall time
        line = [x for x in log[0].split("\n") if "Total wall time" in x][0]
        rawtime = line.split(":", 1)[-1].strip()
        wall_time = utils.timestr2seconds(rawtime)

        # Flux submit with ranks (this is super jank)
        line = [x for x in log[0].split("\n") if "flux submit" in x][-1]
        ranks = int([x for x in line.split(" ") if "-n" in x][0].replace("-n", ""))

        # The last line has the total time to run
        try:
            times = json.loads(pieces[-1].split("\n")[-1])
        except:
            continue

        # The experiment is a summary of the size and x,y,z
        experiment = f"size-{groups['size']}"
        total_time = times["total_time"]

        # We just care about times for the data frame
        df.loc[idx, :] = [
            ranks,
            size,
            x,
            y,
            z,
            experiment,
            scheduler,
            wall_time,
            total_time,
        ]
        idx += 1
    return df


def make_plot(
    df,
    title,
    tag,
    ydimension,
    xdimension,
    palette,
    xlabel,
    ylabel,
    ext="pdf",
    plotname="lammps",
    plot_type="violin",
    hue="experiment",
    outdir="img",
):
    """
    Helper function to make common plots.
    """
    plotfunc = sns.boxplot
    if plot_type == "violin":
        plotfunc = sns.violinplot

    ext = ext.strip(".")
    plt.figure(figsize=(20, 12))
    sns.set_style("dark")
    ax = plotfunc(
        x=xdimension, y=ydimension, hue=hue, data=df, whis=[5, 95], palette=palette
    )
    plt.title(title)
    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel(ylabel, fontsize=16)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=14)
    ax.set_yticklabels(ax.get_yticks(), fontsize=14)
    plt.savefig(os.path.join(outdir, f"{tag}_{plotname}.{ext}"))
    plt.clf()


if __name__ == "__main__":
    main()
