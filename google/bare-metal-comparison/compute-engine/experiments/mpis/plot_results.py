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

    # Let's save the following, with runid as index
    columns = [
        "minicluster_size",
        "mpitype",
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
        _, mpitype, uid, _ = runid.split(os.sep)
        minicluster_size = int(uid.split('_')[1])
        analysis_name = uid.split('_', 2)[-1]

        # Runtime will be in fluxinfo for hostname, lammps log for lammps
        runtime = item['fluxinfo']['runtime']
        ranks = item['fluxinfo']['ntasks']

        datum = [
            minicluster_size,
            mpitype,
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

    # Create a column that has affinity + mpi type
    suffix =  ["-noaff" if "noaff" in x.rsplit('-')[-1] else "" for x in df['analysis'].tolist()]
    prefix = df['mpitype'].tolist()
    df['name'] = [prefix[i] + suffix[i] for i in range(len(suffix))]

#    import IPython
#    IPython.embed()
#    sys.exit()

    # We want to compare ompi vs mpich for each of the affinity vs no affinity
    # Let's split into data frames based on the analysis first and go from there...
    df1 = df[df['analysis'].isin(['hello_usempi', 'hello_usempi-noaff'])]
    df1.to_csv(os.path.join(outdir, "hello_usempi-df.csv"))

    df2 = df[df['analysis'].isin(['ring_c', 'ring_c-noaff'])]
    df2.to_csv(os.path.join(outdir, "ring_c-df.csv"))

    df3 = df[df['analysis'].isin(['ring_usempi', 'ring_usempi-noaff'])]
    df3.to_csv(os.path.join(outdir, "ring_usempi-df.csv"))

    df4 = df[df['analysis'].isin(['hello_cxx', 'hello_cxx-noaff'])]
    df4.to_csv(os.path.join(outdir, "hello_cxx-df.csv"))

    df5 = df[df['analysis'].isin(['hello_c', 'hello_c-noaff'])]
    df5.to_csv(os.path.join(outdir, "hello_c-df.csv"))

    df6 = df[df['analysis'].isin(['ring_mpifh', 'ring_mpifh-noaff'])]
    df6.to_csv(os.path.join(outdir, "ring_mpifh-df.csv"))

    df7 = df[df['analysis'].isin(['connectivity_c', 'connectivity_c-noaff'])]
    df7.to_csv(os.path.join(outdir, "connectivity_c-df.csv"))
    
    # Plot each!
    colors = sns.color_palette("hls", 8)
    hexcolors = colors.as_hex()
    types = list(df1.name.unique())

    # ALWAYS double check this ordering, this
    # is almost always wrong and the colors are messed up
    palette = collections.OrderedDict()
    for t in types:
        palette[t] = hexcolors.pop(0)

    # Let's make a plot that shows distributions of the times by the cluster size, across all
    make_plot(
        df1,
        title="Hello Use MPI Time mpich vs openmpi, w/ and w/o per task affinity",
        tag="hello_usempi",
        ydimension="runtime",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="name",
        plot_type="bar"
    )

    make_plot(
        df2,
        title="Ring C Time mpich vs openmpi, w/ and w/o per task affinity",
        tag="ring_c",
        ydimension="runtime",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="name",
        plot_type="bar"
    )

    make_plot(
        df3,
        title="Ring UseMPI Time mpich vs openmpi, w/ and w/o per task affinity",
        tag="ring_usempi",
        ydimension="runtime",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="name",
        plot_type="bar"
    )

    make_plot(
        df4,
        title="Hello CXX Time mpich vs openmpi, w/ and w/o per task affinity",
        tag="hello_cxx",
        ydimension="runtime",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="name",
        plot_type="bar"
    )

    make_plot(
        df5,
        title="Hello C Time mpich vs openmpi, w/ and w/o per task affinity",
        tag="hello_c",
        ydimension="runtime",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="name",
        plot_type="bar"
    )

    make_plot(
        df6,
        title="Ring MPIfh Time mpich vs openmpi, w/ and w/o per task affinity",
        tag="ring_mpifh",
        ydimension="runtime",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="name",
        plot_type="bar"
    )

    make_plot(
        df7,
        title="Connectivity C Time mpich vs openmpi, w/ and w/o per task affinity",
        tag="connectivity_c",
        ydimension="runtime",
        palette=palette,
        outdir=outdir,
        ext=ext,
        plotname=plotname,
        hue="name",
        plot_type="bar"
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
