#!/usr/bin/env python3

import os
import argparse
import re
import sys
import pandas
import seaborn as sns
import matplotlib.pyplot as plt

here = os.path.dirname(os.path.abspath(__file__))


def recursive_find(base, pattern="^(RTT[.]csv)$"):
    """
    Recursively find lammps output files.
    """
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            if re.search(pattern, filename):
                yield os.path.join(root, filename)


def plot_outputs(results, plotname, ext="png", outdir="img"):
    """
    Parse results.json into dataframe and plots to save.
    """
    # Keep a flat data frame with all results
    data = []
    columns = ["uid", "time", "tasks"]
    for result in results:
        # netmark-experiment-size-64
        uid = os.path.basename(os.path.dirname(result))
        if uid.startswith("_"):
            continue
        raw = pandas.read_csv(result, header=None)
        tasks = int(uid.rsplit("-", 1)[-1])

        # Save a heatmap of the particular run
        plt.figure(figsize=(36, 36))
        sns.heatmap(raw, cmap="BrBG", annot=True)
        plt.title(f"MPI Connection Times for {tasks} Tasks on Google Batch")
        plt.savefig(
            os.path.join(outdir, f"{uid}-heatmap.pdf"), dpi=300, bbox_inches="tight"
        )
        plt.clf()

        # Add all data (minus diagonals)
        for r, row in raw.iterrows():
            for c, value in enumerate(row.values):
                if r == c:
                    continue
                assert value != 0
                data.append([uid, value, tasks])

    df = pandas.DataFrame(data, columns=columns)

    # Save raw data frame
    df.to_csv(os.path.join(outdir, "experiment-times.csv"))

    # We need colors!
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()

    palette = {}
    tasks_sorted = sorted(list(df.tasks.unique()))
    for key in tasks_sorted:
        palette[key] = hexcolors.pop(0)

    make_plot(
        df,
        title="MPI Rank Communication Times Across Cluster Sizes",
        tag="mpi_ranks_communication_times",
        ydimension="time",
        xdimension="tasks",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="tasks",
        plot_type="bar",
        xlabel="Experiment Size",
        ylabel="Time",
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
        "--data", help="data directory", default=os.path.join(here, "data")
    )
    parser.add_argument(
        "-p",
        "--plotname",
        default="netmark",
        help="base name for plot output files",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        dest="outdir",
        help="Output directory for result images.",
        default=os.path.join(here, "img"),
    )
    parser.add_argument(
        "-e",
        "--extension",
        dest="extension",
        default="png",
        help="image extension to use (defaults to png)",
    )
    return parser


def main():
    """
    Read in results json, and make plots.
    """
    parser = get_parser()
    args = parser.parse_args()

    # Both files must exist
    for filename in [args.data]:
        if not os.path.exists(filename):
            sys.exit(f"{filename} does not exist.")

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    # Read in separately!
    data = list(recursive_find(args.data))
    print(f"Found {len(data)} RTT.csv files.")
    plot_outputs(data, args.plotname, ext=args.extension, outdir=args.outdir)


if __name__ == "__main__":
    main()
