#!/usr/bin/env python3

import fluxcloud.utils as utils
import seaborn as sns
import pandas
import os

sns.set_theme()

here = os.path.dirname(os.path.abspath(__file__))


def parse_points(line, machine_type):
    """
    Parse a line of points into int, float, string
    """
    points = [x.strip() for x in line.split(" ", 1)] + [machine_type]
    points = [int(points[0]), float(points[1]), points[2]]
    return points


def main():
    # organize by analysis then machine type
    # Each data file has two columns, with comments up until last description line (with column headers)
    data = {}
    headers = {}
    for machine_type in os.listdir(os.path.join(here, "data")):
        data_dir = os.path.join(here, "data", machine_type)
        for datafile in utils.recursive_find(data_dir, "log.out"):
            analysis_name = os.path.basename(os.path.dirname(datafile))

            lines = utils.read_file(datafile).split("\n")
            description = []
            line = None
            while True:
                last_line = line
                line = lines.pop(0)
                if not line.startswith("#"):
                    break

            # When we get here, last line has column headers, line is first data
            # We only need to derive headers once for an analysis
            if analysis_name not in data:
                h = [
                    x.strip()
                    for x in last_line.strip("#").strip().split(" ", 1)
                    if x.strip()
                ]
                h.append("Machine Type")
                headers[analysis_name] = h
                data[analysis_name] = []

            points = parse_points(line, machine_type)
            data[analysis_name].append(parse_points(line, machine_type))
            while lines:
                line = lines.pop(0)
                if not line.strip():
                    break
                data[analysis_name].append(parse_points(line, machine_type))

    # Save raw data and plots
    results_dir = os.path.join(here, "results")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    for analysis_name, lines in data.items():
        print(analysis_name)
        df = pandas.DataFrame(lines, columns=headers[analysis_name])
        results_file = os.path.join(results_dir, f"{analysis_name}.csv")
        df.to_csv(results_file)
        g = plot(df)
        graph_file = os.path.join(results_dir, f"{analysis_name}.png")
        g.savefig(graph_file)


def plot(df):
    g = sns.lmplot(
        data=df,
        x=df.columns[0],
        y=df.columns[1],
        hue=df.columns[2],
    )
    g.set_axis_labels(df.columns[0], df.columns[1])
    return g


if __name__ == "__main__":
    main()
