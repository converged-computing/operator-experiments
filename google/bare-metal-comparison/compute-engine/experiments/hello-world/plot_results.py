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
        "runtime",
        "analysis",
        "ranks",
    ]

    # Let's first organize distributions of times
    data = []
    index = []

    for logfile, item in raw["results"].items():
        # Split at the data directory to get the run id, and remove log
        runid = logfile.split("data/")[-1].replace(".log", "")        
        index.append(runid)

        # size_5_hostname_noaffinity
        _, uid, _ = runid.split(os.sep)
        minicluster_size = int(uid.split('_')[1])
        analysis_name = uid.split('_', 2)[-1]

        # Runtime will be in fluxinfo for hostname, lammps log for lammps
        if "hostname" in analysis_name:
            assert item['fluxinfo']['success']
            runtime = item['fluxinfo']['runtime']
            ranks = item['fluxinfo']['ntasks']
        else:
            runtime = item['total_wall_time_seconds']
            ranks = item['ranks']

        datum = [
            minicluster_size,
            runtime,
            analysis_name,
            ranks
        ]
        data.append(datum)

    # Assemble the data frame, index is the runids
    df = pandas.DataFrame(data, columns=columns)
    df.index = index

    # Save raw data frame
    df.to_csv(os.path.join(outdir, "results-df.csv"))

    # Let's split into comparing hostname and lammps
    # LOOK AT THESE PANDAS SKILLZ
    # Actually I die a little inside every time I have to remember 
    # how to do something in pandas XD
    ldf = df[df['analysis'].isin(['lammps_small', 'lammps_nocpuaff'])]
    ldf.to_csv(os.path.join(outdir, "lammps-df.csv"))

    hdf = df[~df['analysis'].isin(['lammps_small', 'lammps_nocpuaff'])]
    hdf.to_csv(os.path.join(outdir, "hostname-df.csv"))
    
    # Plot each of hostname and lammps
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()
    analyses = list(ldf.analysis.unique())
    analyses.sort()

    palette = {}
    for a in analyses:
        palette[a] = hexcolors.pop(0)

    # Let's make a plot that shows distributions of the times by the cluster size, across all
    make_plot(
        ldf,
        title="End to End Wall Time Reported by LAMMPS",
        tag="lammps_time",
        ydimension="runtime",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="analysis",
    )

    # Now let's do hostnames
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()
    analyses = list(hdf.analysis.unique())
    analyses.sort()

    palette = {}
    for a in analyses:
        palette[a] = hexcolors.pop(0)

    make_plot(
        hdf,
        title="Hostname Runtimes",
        tag="hostname_time",
        ydimension="runtime",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="analysis",
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
