#!/usr/bin/env python3

import argparse
import os
import seaborn as sns
from metricsoperator.metrics import get_metric
import matplotlib.pyplot as plt
import pandas
import re

here = os.path.abspath(os.path.dirname(__file__))

plt.style.use("bmh")


def recursive_find(base, pattern=".*"):
    """
    Recursively find output files.
    """
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            if re.search(pattern, filename):
                yield os.path.join(root, filename)


def read_file(filename):
    with open(filename, "r") as fd:
        output = fd.read()
    return output


def get_parser():
    parser = argparse.ArgumentParser(
        description="Run OSU Benchmarks Metric and Get Output",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--out",
        help="json file to save results",
        default=os.path.join(here, "metrics.json"),
    )
    return parser


def main():
    """
    Run a job.
    """
    parser = get_parser()
    args, _ = parser.parse_known_args()
    file_dir = os.path.join(here, "logs")

    # Derive metric handle (empty without a spec)
    m = get_metric("network-osu-benchmark")()

    # Directory for plotting results
    img = os.path.join(here, "img")
    if not os.path.exists(img):
        os.makedirs(img)

    # Read in output files and organize data frames by result title
    results = {}
    idxs = {}
    columns = {}
    for filename in recursive_find(file_dir):
        iteration = int(os.path.basename(filename).split("-")[-1].split(".")[0])
        output = read_file(filename)
        result = m.parse_log(output)
        for r in result["data"]:
            slug = r["header"][0].replace("#", "").strip().replace(" ", "-")
            if slug not in results:
                results[slug] = pandas.DataFrame(columns=r["columns"] + ["iter"])
                idxs[slug] = 0
                columns[slug] = {"x": r["columns"][0], "y": r["columns"][1]}
            for datum in r["matrix"]:
                results[slug].loc[idxs[slug], :] = datum + [iteration]
                idxs[slug] += 1

    # Now plot each dataframe
    for slug, df in results.items():
        x = columns[slug]["x"]
        y = columns[slug]["y"]
        df.to_csv(os.path.join(img, f"{slug}.csv"))

        # for sty in plt.style.available:
        title = slug.replace("-", " ")
        ax = sns.lineplot(data=df, x=x, y=y, hue="iter", markers=True, dashes=True)
        plt.title(title)
        memo = "higher is better"
        if "latency" in y.lower():
            memo = "lower is better"
        ax.set_xlabel("Packet size (bits) logscale", fontsize=16)
        ax.set_ylabel(y + " " + memo + " logscale", fontsize=16)
        ax.set_xticklabels(ax.get_xmajorticklabels(), fontsize=14)
        ax.set_yticklabels(ax.get_yticks(), fontsize=14)
        plt.xscale("log")
        plt.yscale("log")
        plt.tight_layout()
        plt.savefig(os.path.join(img, f"{slug}.png"))
        plt.clf()


if __name__ == "__main__":
    main()
