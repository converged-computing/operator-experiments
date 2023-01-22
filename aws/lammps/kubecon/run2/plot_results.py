#!/usr/bin/env python3

import os
import argparse
import json
import re
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


def plot_outputs(raw, plotname, slot_per_pod, ext="pdf"):
    """
    Parse results.json into dataframe and plots to save.
    """

    # Let's save the following, with runid as index
    columns = [
        "minicluster_size",
        "fluxsubmit_time",
        "lammps_time",
        "ranks",
        "timesteps_per_second",
        "loop_time",
    ]

    # Let's first organize distributions of times
    data = []
    index = []
    for logfile, item in raw.items():

        # Split at the data directory to get the run id, and remove log
        runid = logfile.split("data/")[-1].replace("/log.out", "")
        index.append(runid)

        # This is how flux-cloud organized the output
        minicluster_size = runid.rsplit("size-", 1)[-1]
        data.append(
            [
                minicluster_size,
                item["fluxsubmit_wall_time_seconds"],
                item["total_wall_time_seconds"],
                item["ranks"],
                item["timesteps_per_second"],
                item["loop_time"],
            ]
        )

    # Assemble the data frame, index is the runids
    df = pandas.DataFrame(data, columns=columns)
    df.index = index

    # Save raw data
    df.to_csv("results-df.csv")

    # We need colors!
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()

    palette = {}
    for size in df.minicluster_size.unique():
        palette[size] = hexcolors.pop(0)

    # Let's make a plot that shows distributions of the times by the cluster size
    # First for the flux mini cluster wall times
    make_plot(
        df,
        "Flux MiniCluster Wall Time",
        "fluxsubmit_walltime",
        "fluxsubmit_time",
        palette,
        ext=ext,
        plotname=plotname,
    )
    make_plot(
        df,
        "Lammps Wall Time",
        "lammps_walltime",
        "lammps_time",
        palette,
        ext=ext,
        plotname=plotname,
    )
    make_plot(
        df,
        "Timesteps per Second",
        "timesteps_per_second",
        "timesteps_per_second",
        palette,
        ext=ext,
        plotname=plotname,
    )


def make_plot(df, title, tag, ydimension, palette, ext="pdf", plotname="lammps"):
    """
    Helper function to make common plots.
    """
    ext = ext.strip(".")
    plt.figure(figsize=(32, 32))
    sns.set_style("dark")
    ax = sns.boxplot(
        x="ranks",
        y=ydimension,
        hue="minicluster_size",
        data=df,
        whis=[5, 95],
        palette=palette,
    )
    plt.title("Timesteps per Second")
    plt.legend([], [], frameon=False)
    ax.set_xlabel("MPI Ranks", fontsize=20)
    ax.set_ylabel("Time (seconds)", fontsize=20)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=18)
    ax.set_yticklabels(ax.get_yticks(), fontsize=18)
    plt.savefig(f"{tag}_{plotname}.{ext}")
    plt.clf()


def get_parser():
    """
    Process results file into plots.
    """
    parser = argparse.ArgumentParser(description="Plot LAMMPS outputs")
    parser.add_argument(
        "results_json", help="results json file", default="results.json", nargs="?"
    )
    parser.add_argument(
        "-p",
        "--plotname",
        default="lammps",
        help="base name for plot output files",
    )
    parser.add_argument(
        "-e",
        "--extension",
        dest="extension",
        default="pdf",
        help="image extension to use (defaults to pdf)",
    )
    parser.add_argument(
        "--spp",
        "--slot_per_pod",
        dest="slot_per_pod",
        default=False,
        action="store_true",
        help="generate slot per pod plot",
    )
    return parser


def main():
    """
    Read in results json, and make plots.
    """
    parser = get_parser()
    args = parser.parse_args()
    if not os.path.exists(args.results_json):
        sys.exit(f"{args.results_json} does not exist.")
    data = read_json(args.results_json)
    plot_outputs(data, args.plotname, args.slot_per_pod, ext=args.extension)


if __name__ == "__main__":
    main()
