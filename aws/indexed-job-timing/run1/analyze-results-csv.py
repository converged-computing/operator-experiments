#!/usr/bin/env python3

# Analyze results for pod events and make summary plots.
import argparse
import collections
import json
import os
import re
import sys
from datetime import datetime, timezone

import matplotlib.pylab as plt
import pandas
import seaborn as sns

plt.style.use("bmh")

# Save data here
here = os.path.dirname(os.path.abspath(__file__))

# Assume input directory is data
data = os.path.join(here, "data")
results = os.path.join(here, "img")



def get_parser():
    parser = argparse.ArgumentParser(
        description="Results Analyzer (just csv)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--outdir", help="Output directory", default=results)
    parser.add_argument("data", help="Input csv with results")
    return parser


def main():
    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, _ = parser.parse_known_args()

    if not args.data or not os.path.exists(args.data):
        sys.exit("Please provide the data input directory as the only argument")

    # Experiment output files
    df = pandas.read_csv(args.data, index_col=0)

    # plot the results!
    plot_data(df, args.outdir)


def plot_data(df, outdir):
    """
    Plot results into data frame
    """
    # Plot each!
    colors = sns.color_palette("hls", 16)
    hexcolors = colors.as_hex()
    types = list(df["experiment"].unique())
    types.sort()

    # ALWAYS double check this ordering, this
    # is almost always wrong and the colors are messed up
    palette = collections.OrderedDict()
    for t in types:
        palette[t] = hexcolors.pop(0)

    # Create a plot for each pod type, colored by size
    # This shows the distribution of times across sizes
    for event in df.event.unique():
        slug = event.lower()
        subset = df[df.event == event]
        make_plot(
            subset,
            title=f"Pod vs. Indexed Job {event} Times (4 x m5.16xlarge)",
            tag=f"times-experiment-{slug}",
            ydimension="time_seconds",
            xdimension="size",
            palette=palette,
            outdir=outdir,
            ext="png",
            plotname=f"times-experiments-{slug}",
            hue="experiment",
            plot_type="bar",
            xlabel="Number of pods",
            ylabel="Time (seconds)",
        )


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
    hue="ranks",
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
