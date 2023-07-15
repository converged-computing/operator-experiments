#!/usr/bin/env python3

import re
import os
import collections
import argparse
import json
import sys
import pandas
import seaborn as sns
import matplotlib.pyplot as plt


def read_json(filename):
    """
    Read a file into a text blob.
    """
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content

def recursive_find(base, pattern="json"):
    """
    Recursively find lammps output files.
    """
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            if re.search(pattern, filename):
                yield os.path.join(root, filename)


def plot_outputs(df, plotname="lammps", ext="pdf", outdir=None):
    """
    Parse results.json into dataframe and plots to save.
    """
    outdir = outdir or "img"

    # Plot each!
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()
    types = list(df.experiment.unique())

    # ALWAYS double check this ordering, this
    # is almost always wrong and the colors are messed up
    palette = collections.OrderedDict()
    for t in types:
        palette[t] = hexcolors.pop(0)

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Let's make a plot that shows distributions of the times by the cluster size, across all
    make_plot(
        df,
        title="LAMMPS Times with and Without EFA",
        tag="lammps-efa",
        ydimension="time",
        xdimension="experiment",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="experiment",
        plot_type="bar",
        xlabel="Experiment",
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
    hue="minicluster_size",
    outdir="img",
    add_legend=True,
):
    """
    Helper function to make common plots.
    """
    plotfunc = sns.boxplot
    if plot_type == "violin":
        plotfunc = sns.violinplot

    ext = ext.strip(".")
    plt.figure(figsize=(12, 12))
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


def get_parser():
    """
    Process results file into plots.
    """
    parser = argparse.ArgumentParser(description="Plot LAMMPS outputs")
    parser.add_argument(
        "data", help="data directory", default="data", nargs="?"
    )
    parser.add_argument(
        "-o",
        "--outdir",
        dest="outdir",
        help="Output directory for result images.",
    )
    parser.add_argument(
        "-e",
        "--extension",
        dest="extension",
        default="png",
        help="image extension to use (defaults to pdf)",
    )
    return parser

def read_data(dirname):
    """
    Read data into dataframe for plotting.
    """
    df = pandas.DataFrame(columns=["experiment", "iter", "time"])   
    idx = 0
    for datafile in recursive_find(dirname):
        if not os.path.basename(datafile).startswith('lammps'):
            continue
        if "test-size-1" in datafile:
            continue
        res = read_json(datafile)
        iter = int(os.path.basename(datafile).split('-')[1])
        # Kind of janky!
        experiment = os.path.basename(os.path.dirname(os.path.dirname(datafile)))
        df.loc[idx, :] = [experiment, iter, res['runtime']]
        idx +=1

    df.to_csv('data/results.csv')
    return df

def main():
    """
    Read in results json, and make plots.
    """
    parser = get_parser()
    args = parser.parse_args()
    if not os.path.exists(args.data):
        sys.exit(f"{args.data} does not exist.")
    data = read_data(args.data)
    plot_outputs(data, ext=args.extension, outdir=args.outdir)

if __name__ == "__main__":
    main()
