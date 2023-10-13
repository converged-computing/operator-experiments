#!/usr/bin/env python3

# Launch jobs and watch for pods events. We only care about the ids and when they are created
# and then we can compare between cases. Since we have a small testing cluster here (kind)
# we will only do small tests.
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


def str_to_datetime(datetime_str_obj):
    return datetime.strptime(datetime_str_obj, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )


def recursive_find(base, pattern=None):
    """
    Find filenames that match a particular pattern, and yield them.
    """
    # We can identify modules by finding module.lua
    for root, folders, files in os.walk(base):
        for file in files:
            fullpath = os.path.abspath(os.path.join(root, file))

            if pattern and not re.search(pattern, fullpath):
                continue
            yield fullpath


def write_json(obj, path):
    """
    write json to file
    """
    with open(path, "w") as fd:
        fd.write(json.dumps(obj, indent=4))


def get_parser():
    parser = argparse.ArgumentParser(
        description="Pod Event Watcher",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--outdir", help="Path for the parsed results", default=results)
    parser.add_argument("data", help="Input data directory with experiments")
    return parser


def read_json(filename):
    with open(filename, "r") as file:
        content = json.loads(file.read())
    return content


def organize_timestamps(events):
    """
    Break events into listings by type
    """
    # To start, we have no events known. Keep track of when first seen, and when transitioned
    timestamps = {}
    for event in events:
        conditions = event["event"]["raw_object"]["status"].get("conditions", [])
        for condition in conditions:
            if condition["type"] not in timestamps:
                timestamps[condition["type"]] = []
            transition_time = str_to_datetime(condition["lastTransitionTime"])
            timestamps[condition["type"]].append(
                {
                    "lastTransitionTime": transition_time,
                    "status": condition["status"] == "True",
                }
            )

    return timestamps


def get_created_timestamp(events):
    """
    Get a parsed created_at timestamp.

    Raise hell if we find that one is different.
    """
    created_timestamp = None
    for event in events:
        new_created_timestamp = event["event"]["raw_object"]["metadata"][
            "creationTimestamp"
        ]
        created_at = str_to_datetime(new_created_timestamp)
        if created_timestamp is not None and new_created_timestamp != created_timestamp:
            print(created_timestamp)
            print(new_created_timestamp)
            raise ValueError("Pod labeled with different creation timestamps!")
    return created_at


def read_data(files):
    """
    parse results into pandas data frame
    """
    df = pandas.DataFrame(
        columns=["time_seconds", "event", "pod", "size", "experiment", "iteration"]
    )
    idx = 0
    for filename in files:
        res = read_json(filename)
        size = res["size"]
        experiment = res["experiment"].rsplit("-", 1)[0]
        iteration = res["iteration"]

        # Across pod events (create and delete total times)
        for key in ["watch_create", "watch_delete"]:
            df.loc[idx, :] = [
                res["times"][key],
                key,
                "all",
                size,
                experiment,
                iteration,
            ]
            idx += 1

        # Events organized by pod
        for pod_name, events in res["events"]["create"].items():
            # Creation timestamp is time 0
            timestamps = organize_timestamps(events)
            # Now further refine! Always calculate offset from created at for total time

            # This is always the same (throw a massive error if not)
            created_at = get_created_timestamp(events)

            # The first occurrence of PodScheduled True is when it is scheduled
            # We assume a pod is scheduled once. This should get the first True
            for key in ["PodScheduled", "Initialized", "Ready", "ContainersReady"]:
                offset = get_first_occurrence(timestamps[key], True, created_at)
                seconds = offset.total_seconds()
                # print(f"Pod {pod_name} had status {key} in {seconds} seconds")

                # columns=["time_seconds", "event", "pod", "size", "experiment", "iteration"]
                df.loc[idx, :] = [seconds, key, pod_name, size, experiment, iteration]
                idx += 1
    return df


def get_first_occurrence(group, status, created_at):
    scheduled_at = [x for x in group if x["status"] == status][0]
    scheduled_time = scheduled_at["lastTransitionTime"]
    return scheduled_time - created_at


def main():
    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, _ = parser.parse_known_args()

    if not args.data or not os.path.exists(args.data):
        sys.exit("Please provide the data input directory as the only argument")

    # Experiment output files
    files = list(recursive_find(args.data, "[.]json$"))

    # Generate a pandas data frame of parsed results
    print(f"🤓️ Reading data for {len(files)} files...")
    df = read_data(files)
    groups = df.groupby(["event", "experiment", "size"]).mean()
    groups.to_csv(os.path.join(args.outdir, "pod-times-grouped.csv"))
    print(groups)
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    df.to_csv(os.path.join(args.outdir, "pod-times.csv"))

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
            title=f"Pod vs. Indexed Job {event} Times (local run with Kind)",
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
