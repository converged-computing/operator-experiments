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


def plot_outputs(raw, mpi_operator, plotname, ext="pdf"):
    """
    Parse results.json into dataframe and plots to save.
    """

    # Let's save the following, with runid as index
    columns = [
        "minicluster_size",
        "name",  # id for the mini cluster, should be mini-cluster-<size>
        "lammps_time",
        "ranks",
        "timesteps_per_second",
    ]
    cluster_times = {
        x.replace("minicluster-run-", ""): t
        for x, t in raw["meta"]["times"].items()
        if x.startswith("minicluster-run")
    }

    # Let's first organize distributions of times
    data = []
    index = []
    for logfile, item in raw["results"].items():

        # Split at the data directory to get the run id, and remove log
        runid = logfile.split("data/")[-1].replace("/log.out", "")
        dirname = os.path.basename(runid)

        # Don't include container we were pulling
        if dirname.startswith("_"):
            continue
        index.append(runid)

        # This is how flux-cloud organized the output
        minicluster_size = int(runid.rsplit("size-", 1)[-1])
        datum = [
            minicluster_size,
            f"minicluster-{minicluster_size}",
            item["total_wall_time_seconds"],
            item["ranks"],
            item["timesteps_per_second"],
        ]
        data.append(datum)

    # Assemble the data frame, index is the runids
    # This first will be to look at cluster size (we don't have for mpi-operator)
    df = pandas.DataFrame(data, columns=columns)
    df.index = index

    # Save raw data frame
    df.to_csv("results-df.csv")

    # Add the mpi operator times!
    [x.append("flux-operator") for x in data]

    # Give each job run a unique via counts for the index
    counts = {}
    for item in mpi_operator:
        if item["scheduler"] != "default-scheduler":
            continue
        size = item["pods"]
        if size not in counts:
            counts[size] = 0
        counts[size] += 1
        count = counts[size]
        runid = f"lmp-mpi-operator-{size}-{count}"
        index.append(runid)
        datum = [
            item["pods"],  # this is the mpi operator cluster size
            f"mpi-operator-{item['pods']}",
            # This end to end time is different - it contains pod creations I think?
            item["lammps_time"],
            item["ranks"],
            item["timesteps/s"],
            "mpi-operator",
        ]
        data.append(datum)

    columns.append("operator_name")
    df = pandas.DataFrame(data, columns=columns)
    df.index = index

    # Save raw data frame
    df.to_csv("results-combined-df.csv")

    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()

    palette = {}
    for size in df.operator_name.unique():
        palette[size] = hexcolors.pop(0)

    # Sort by size
    palette = dict(sorted(palette.items()))

    make_plot(
        df,
        title="Lammps Wall Time",
        tag="walltime",
        ydimension="lammps_time",
        palette=palette,
        ext=ext,
        plotname=plotname,
        hue="operator_name",
    )
    make_plot(
        df,
        title="Timesteps per Second",
        tag="timesteps_per_second",
        ydimension="timesteps_per_second",
        palette=palette,
        ext=ext,
        plotname=plotname,
        hue="operator_name",
        plot_type="box",
    )


def make_plot(
    df,
    title,
    tag,
    ydimension,
    palette,
    ext="pdf",
    plotname="lammps",
    plot_type="violin",
    hue="minicluster_size",
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
        x="ranks",
        y=ydimension,
        hue=hue,
        data=df,
        whis=[5, 95],
        palette=palette,
    )
    plt.title(title)
    plt.legend([], [], frameon=False)
    ax.set_xlabel("MPI Ranks", fontsize=16)
    ax.set_ylabel("Time (seconds)", fontsize=16)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=14)
    ax.set_yticklabels(ax.get_yticks(), fontsize=14)
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles, list(palette))
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
        "--mpi-operator",
        help="mpi operator results file",
        default="mpi_operator_results.json",
        nargs="?",
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
    mpi_operator = read_json(args.mpi_operator)
    plot_outputs(data, mpi_operator, args.plotname, ext=args.extension)


if __name__ == "__main__":
    main()
