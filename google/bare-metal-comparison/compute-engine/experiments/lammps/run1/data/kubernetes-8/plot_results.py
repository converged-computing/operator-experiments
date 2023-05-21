#!/usr/bin/env python3

import os
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

    # Let's save the following, with runid as index
    columns = [
        "minicluster_size",
        "name",  # id for the mini cluster, should be mini-cluster-<size>
        "lammps_time",
        "flux_info_time",
        "ranks",
        "timesteps_per_second",
    ]

    # Let's first organize distributions of times
    data = []
    index = []
    for logfile, item in raw["results"].items():
        # Split at the data directory to get the run id, and remove log
        runid = logfile.split("data/")[-1].replace(".log", "")
        index.append(runid)

        _, minicluster_size, _ = runid.split(os.sep)
        minicluster_size = int(minicluster_size.split('_')[1])
        datum = [
            minicluster_size,
            f"minicluster-{minicluster_size}",           
            item["total_wall_time_seconds"],
            item['fluxinfo']['runtime'],
            item["ranks"],
            item["timesteps_per_second"],
        ]
        data.append(datum)

    # Assemble the data frame, index is the runids
    df = pandas.DataFrame(data, columns=columns)
    df.index = index

    # Save raw data frame
    df.to_csv(os.path.join(outdir, "results-df.csv"))

    # We need colors!
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()
    sizes = list(df.minicluster_size.unique())
    sizes.sort()

    palette = {}
    for size in sizes:
        palette[size] = hexcolors.pop(0)

    # Let's make a plot that shows distributions of the times by the cluster size, across all
    make_plot(
        df,
        title="End to End Wall Time Reported by LAMMPS",
        tag="lammps_time",
        ydimension="lammps_time",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="minicluster_size",
    )
    make_plot(
        df,
        title="Flux Info Total LAMMPS Job Runtime",
        tag="lammps_job_time",
        ydimension="flux_info_time",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="minicluster_size",
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
    if add_legend:
        ax.legend(handles, list(palette))
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
        default="lammps",
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
