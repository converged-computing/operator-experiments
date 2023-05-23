#!/usr/bin/env python3

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


def plot_outputs(raw, plotname, ext="pdf", outdir=None):
    """
    Parse results.json into dataframe and plots to save.
    """
    outdir = outdir or "img"

    # Each index in results is a different result set.

    # Let's save the following, with runid as index
    columns = [
        "experiment",
        "name",
        "machine_type",
        "increment",
        "direction",
        "iteration",
        "seconds",
        "key",  # key tells us the from -> to node
    ]

    # Let's first organize distributions of times
    data = []
    index = []

    for logfile, item in raw["results"].items():
        # Split at the data directory to get the run id, and remove log
        runid = logfile.split("data/")[-1].replace(".json", "")
        index.append(runid)

        # size_5_hostname_noaffinity
        experiment, name, iteration = runid.split(os.sep)
        increment = int(experiment.split("-")[-1])
        direction = experiment.split("-")[-2]
        machine_type = item["machine_type"]

        for key, seconds in item["times"].items():
            if key in ["create_cluster", "delete_cluster"]:
                datum = [
                    experiment,
                    name,
                    machine_type,
                    increment,
                    key,
                    iteration,
                    seconds,
                    key,
                ]
            else:
                datum = [
                    experiment,
                    name,
                    machine_type,
                    increment,
                    direction,
                    iteration,
                    seconds,
                    key,
                ]
            data.append(datum)

    # Assemble the data frame, index is the runids
    df = pandas.DataFrame(data, columns=columns)

    # Save raw data frame
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    df.to_csv(os.path.join(outdir, "results-df.csv"))

    # Plot 1: cluster creation and deletion times
    # Filter out each of create cluster and delete cluster
    dfcluster = df[df["direction"].isin(["create_cluster", "delete_cluster"])]

    # Plot each!
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()
    types = list(dfcluster.machine_type.unique())

    # ALWAYS double check this ordering, this
    # is almost always wrong and the colors are messed up
    palette = collections.OrderedDict()
    for t in types:
        palette[t] = hexcolors.pop(0)

    # Let's make a plot that shows distributions of the times by the cluster size, across all
    make_plot(
        dfcluster,
        title="Creation times for clusters",
        tag="create_delete_cluster",
        ydimension="seconds",
        xdimension="direction",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="machine_type",
        plot_type="bar",
        xlabel="Creation or Deletion of Cluster",
        ylabel="Time (seconds)",
    )

    # Next remove those from the df!
    df = df[~df["direction"].isin(["create_cluster", "delete_cluster"])]

    # Compare up and down times for each increment
    for i in df.increment.unique():
        df1 = df[df.increment == i]

        colors = sns.color_palette("hls", 8)
        hexcolors = colors.as_hex()
        types = list(df.direction.unique())

        palette = collections.OrderedDict()
        for t in types:
            palette[t] = hexcolors.pop(0)

        # Make a plot that tries to compare add/remove side by side
        make_plot(
            df1,
            title=f"Adding vs. removing {i} node(s), side by side (over 10 clusters each) with outliers",
            tag=f"add_vs_remove_{i}_nodes_with_outliers",
            ydimension="seconds",
            xdimension="machine_type",
            palette=palette,
            outdir=outdir,
            ext=ext,
            plotname=plotname,
            hue="direction",
            plot_type="bar",
            xlabel="Machine Type",
            ylabel="Time (seconds)",
        )

        df1 = df1[df1.seconds <= 300]

        # Make a plot that tries to compare add/remove side by side
        make_plot(
            df1,
            title=f"Adding vs. removing {i} node(s), side by side (over 10 clusters each) without outliers",
            tag=f"add_vs_remove_{i}_nodes_no_outliers",
            ydimension="seconds",
            xdimension="machine_type",
            palette=palette,
            outdir=outdir,
            ext=ext,
            plotname=plotname,
            hue="direction",
            plot_type="bar",
            xlabel="Machine Type",
            ylabel="Time (seconds)",
        )

    # First look at the cluster going up or down by 1
    for dirname in ["up", "down"]:
        df1 = df[df["direction"] == "up"]
        df1 = df1[df1["increment"] == 1]

        # Plot by iteration since these are different clusters
        colors = sns.color_palette("hls", 10)
        hexcolors = colors.as_hex()
        types = list(df1.machine_type.unique())

        # ALWAYS double check this ordering, this
        # is almost always wrong and the colors are messed up
        palette = collections.OrderedDict()
        for t in types:
            palette[t] = hexcolors.pop(0)

        # This was a test run
        df1 = df1[df1.name != "as-cluster-1"]

        # For each unique experiment, do a plot
        term = "add" if dirname == "up" else "remove"
        make_plot(
            df1,
            title=f"Time to {term} one node to the cluster (over 10 clusters)",
            tag=f"{term}_one_node_outliers",
            ydimension="seconds",
            xdimension="machine_type",
            palette=palette,
            outdir=outdir,
            ext=ext,
            plotname=plotname,
            hue="machine_type",
            plot_type="bar",
            xlabel="Machine Type",
            ylabel="Time (seconds)",
        )
        # Remove the HUGE outliers
        df1 = df1[df1.seconds <= 100]
        make_plot(
            df1,
            title=f"Time to {term} one node to the cluster (over 10 clusters) (outliers removed)",
            tag=f"{term}_one_node_no_outliers",
            ydimension="seconds",
            xdimension="machine_type",
            palette=palette,
            outdir=outdir,
            ext=ext,
            plotname=plotname,
            hue="machine_type",
            plot_type="bar",
            xlabel="Machine Type",
            ylabel="Time (seconds)",
        )

    # Now we want to understand if order matters!
    # Let's just look at increasing by 1, for c2-standard-8
    df1 = df[df.machine_type == "c2-standard-8"]
    df1 = df1[df1.increment == 1]

    # Create an order column
    orders = [int(x.split("_")[-1]) for x in list(df1.key.values)]
    df1["orders"] = orders
    df1up = df1[df1.direction == "up"]
    df1down = df1[df1.direction == "down"]

    # Up
    ax = sns.lineplot(data=df1up, x="orders", y="seconds", hue="iteration")
    plt.title("Incremental time to add a node (with outliers)")
    ax.set_xlabel("Node index", fontsize=16)
    ax.set_ylabel("Time (seconds)", fontsize=16)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=14)
    ax.set_yticklabels(ax.get_yticks(), fontsize=14)
    plt.savefig(os.path.join(outdir, f"add_node_incremental.{ext}"))
    plt.clf()

    # Remove outlier
    df1up = df1up[df1up.seconds <= 100]
    ax = sns.lineplot(data=df1up, x="orders", y="seconds", hue="iteration")
    plt.title("Incremental time to add a node (without outliers)")
    ax.set_xlabel("Node index", fontsize=16)
    ax.set_ylabel("Time (seconds)", fontsize=16)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=14)
    ax.set_yticklabels(ax.get_yticks(), fontsize=14)
    plt.savefig(os.path.join(outdir, f"add_node_incremental_no_outliers.{ext}"))
    plt.clf()

    # Down
    ax = sns.lineplot(data=df1down, x="orders", y="seconds", hue="iteration")
    plt.title("Incremental time to remove a node (with outliers)")
    ax.set_xlabel("Node index", fontsize=16)
    ax.set_ylabel("Time (seconds)", fontsize=16)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=14)
    ax.set_yticklabels(ax.get_yticks(), fontsize=14)
    plt.savefig(os.path.join(outdir, f"remove_node_incremental.{ext}"))
    plt.clf()

    # Remove outlier
    df1down = df1down[df1down.seconds <= 100]
    ax = sns.lineplot(data=df1down, x="orders", y="seconds", hue="iteration")
    plt.title("Incremental time to remove a node (without outliers)")
    ax.set_xlabel("Node index", fontsize=16)
    ax.set_ylabel("Time (seconds)", fontsize=16)
    ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=14)
    ax.set_yticklabels(ax.get_yticks(), fontsize=14)
    plt.savefig(os.path.join(outdir, f"remove_node_incremental_no_outliers.{ext}"))
    plt.clf()


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
        "results_json", help="results json file", default="results.json", nargs="?"
    )
    parser.add_argument(
        "-p",
        "--plotname",
        default="mpis",
        help="base name for plot output files",
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


def main():
    """
    Read in results json, and make plots.
    """
    parser = get_parser()
    args = parser.parse_args()
    if not os.path.exists(args.results_json):
        sys.exit(f"{args.results_json} does not exist.")

    # Read in separately!
    data = read_json(args.results_json)
    plot_outputs(data, args.plotname, ext=args.extension, outdir=args.outdir)


if __name__ == "__main__":
    main()
