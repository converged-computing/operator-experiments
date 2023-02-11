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

                # x86     zen3       original
def plot_outputs(x86, optimized, not_optimized, plotname, ext="pdf", outdir="img"):
    """
    Parse results.json into dataframe and plots to save.
    """
    # Find common sizes between the two
    sizes_a = set([x['size'] for _,x in x86['meta']['jobs'].items()])
    sizes_b = set([x['size'] for _,x in not_optimized['meta']['jobs'].items()])
    sizes_c = set([x['size'] for _,x in optimized['meta']['jobs'].items()])

    shared_sizes = sizes_a.intersection(sizes_b).intersection(sizes_c)
    if not shared_sizes:
        sys.exit('Optimized and non-optimized data do not share any sizes.')

    # Let's save the following, with runid as index
    columns = [
        "runid",
        "minicluster_size",
        "name",  # id for the mini cluster, should be mini-cluster-<size>
        "fluxsubmit_time",
        "fluxstart_time",
        "lammps_time",
        "ranks",
        "timesteps_per_second",
        "optimization",
    ]

    # Let's first organize distributions of times
    data = []

    def add_results(results, label): 
        """
        Shared function to add results
        """
        # First add optimized
        for logfile, item in results["results"].items():
            # Split at the data directory to get the run id, and remove log
            runid = logfile.split("data/")[-1].replace("/log.out", "")
            dirname = os.path.basename(runid)

            # Don't include container we were pulling, run 0
            if dirname.startswith("_"):
                continue

            # This is how flux-cloud organized the output
            minicluster_size = int(runid.rsplit("size-", 1)[-1])

            if minicluster_size not in shared_sizes:
                continue

            datum = [
                label + "-" + runid,
                minicluster_size,
                f"minicluster-{minicluster_size}",
                item["fluxsubmit_wall_time_seconds"],
                item["fluxstart_wall_time_seconds"],
                item["total_wall_time_seconds"],
                item["ranks"],
                item["timesteps_per_second"],
                label,
            ]
            print(datum)
            data.append(datum)

    add_results(optimized, "optimized (zen3)")
    add_results(not_optimized, "not-optimized (original)")
    add_results(x86, "not-optimized x86 (same container as zen3)")

    # Assemble the data frame, index is the runids
    # This first will be to look at cluster size (we don't have for mpi-operator)
    df = pandas.DataFrame(data, columns=columns)
        
    # Save raw data frame
    df.to_csv(os.path.join(outdir, "results-df.csv"))

    # We need colors!
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()

    palette = {}
    for size in df.optimization.unique():
        palette[size] = hexcolors.pop(0)

    # Let's make a plot that shows distributions of the times by the cluster size, across all
    make_plot(
        df,
        title="LAMMPS Flux Submit (optimized vs. unoptimized)",
        tag="lammps_fluxsubmit_optimization_comparison",
        ydimension="fluxsubmit_time",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="optimization",
        plot_type="box",
    )
    make_plot(
        df,
        title="LAMMPS Flux Start (optimized vs. unoptimized)",
        tag="lammps_fluxstart_optimization_comparison",
        ydimension="fluxstart_time",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="optimization",
        plot_type="box",
    )
    make_plot(
        df,
        title="LAMMPS Wall Time (optimized vs. unoptimized)",
        tag="walltime",
        ydimension="lammps_time",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="optimization",
#        plot_type="box",
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
    plt.savefig(os.path.join(outdir, f"{tag}_{plotname}.{ext}"))
    plt.clf()


def get_parser():
    """
    Process results file into plots.
    """
    parser = argparse.ArgumentParser(description="Plot LAMMPS outputs")
    parser.add_argument(
        "--optimized", help="optimized results json file", default="optimized-zen3-results.json", nargs="?"
    )
    parser.add_argument(
        "--results", help="results json file (x86 build here)", default="results.json", nargs="?"
    )
    parser.add_argument(
        "--non-optimized",
        help="unoptimized results",
        dest="not_optimized",
        default="unoptimized-results.json",
        nargs="?",
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
    
    # Both files must exist
    for filename in args.optimized, args.not_optimized, args.results:
        if not os.path.exists(filename):
            sys.exit(f"{filename} does not exist.")
    
    # Read in separately!
    optimized = read_json(args.optimized)          # zen 3
    not_optimized = read_json(args.not_optimized)  # original
    results = read_json(args.results)              # x86
                 # x86    zen3       original
    plot_outputs(x86=results, optimized=optimized, not_optimized=not_optimized, plotname=args.plotname, ext=args.extension, outdir=args.outdir)

if __name__ == "__main__":
    main()
