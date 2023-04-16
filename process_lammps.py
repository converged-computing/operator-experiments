#!/usr/bin/env python3

import os
import argparse
import json
import re
import sys
import pandas
import seaborn as sns
import matplotlib.pyplot as plt


def recursive_find(base, pattern="^(laamps[.]out|lammps.*[.]out|log[.]out)$"):
    """
    Recursively find lammps output files.
    """
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            if re.search(pattern, filename):
                yield os.path.join(root, filename)


def read_file(filename):
    """
    Read a file into a text blob.
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def read_lines(filename):
    """
    Read lines of a file into a list.
    """
    with open(filename, "r") as fd:
        lines = fd.readlines()
    return lines


def get_first_int(match):
    return int(match.group().strip().split(" ")[0])


def gather_outputs(outdir):

    # Store results by machine / size
    results = {}

    # Handle partial / relative / "." paths
    outdir = os.path.abspath(outdir)
    if not os.path.exists(outdir):
        sys.exit(f"{outdir} does not exist.")

    for file in recursive_find(outdir):
        file_output = os.path.join(outdir, file)
        lines = read_lines(file)

        entry = {}
        while lines:
            line = lines.pop(0)

            # Figure out ranks and threads (in same line)
            match = re.search("[0-9]+ MPI tasks", line)
            if match:
                entry["ranks"] = get_first_int(match)
            match = re.search("[0-9]+ OpenMP threads", line)
            if match:
                entry["threads"] = get_first_int(match)

            match = re.search("(?P<percentage>[0-9]+[.][0-9]+)[%] CPU use with", line)
            if match:
                entry["percentage_cpu"] = float(match.groupdict()["percentage"])
                continue

            if re.search("^(NLocal|Nghost|Neighs)", line):
                category = line.split(":")[0].lower()
                line = line.split(":", 1)[-1].strip()
                ave, line = line.split("ave", 1)
                maxval, line = line.split("max", 1)
                minval, line = line.split("min", 1)
                entry.update(
                    {
                        f"{category}_avg": ave,
                        f"{category}_min": minval,
                        f"{category}_max": maxval,
                    }
                )
                hist = lines.pop(0).split(":")[-1].strip().split(" ")
                entry[f"{category}_hist"] = [int(x) for x in hist]
                continue

            if line.startswith("Total # of neighbors"):
                entry["neighbors"] = float(line.split("=")[-1].strip())
                continue

            if line.startswith("Ave neighs/atom"):
                entry["average_neighbors_per_atom"] = float(line.split("=")[-1].strip())
                continue

            if line.startswith("Neighbor list builds"):
                entry["neighbor_list_builds"] = int(line.split("=")[-1].strip())
                continue

            if line.startswith("Total wall time"):
                entry["total_wall_time"] = line.split(":", 1)[-1].strip()
                continue

            # Dimension of molecular matrix maybe?
            match = re.search(
                "(?P<x>[0-9]+) by (?P<y>[0-9]+) by (?P<z>[0-9]+) MPI processor grid",
                line,
            )
            if match:
                [entry.update({k: int(v)}) for k, v in match.groupdict().items()]
                continue

            # Number of atoms / velocities
            match = re.search("[0-9]+ atoms", line)
            if match and "atoms" not in entry:
                entry["atoms"] = get_first_int(match)
                continue
            match = re.search("[0-9]+ velocities", line)
            if match:
                entry["velocities"] = get_first_int(match)
                continue

            # reading data from CPU
            match = re.search("read_data CPU = (?P<cpu>[0-9]+[.][0-9]+) seconds", line)
            if match:
                entry["read_data_cpu_seconds"] = float(match.groupdict()["cpu"])
                continue

            match = re.search(
                "bounding box extra memory = (?P<mem>[0-9]+[.][0-9]+) MB", line
            )
            if match:
                entry["bounding_box_extra_memory_mb"] = float(match.groupdict()["mem"])
                continue

            match = re.search(
                "replicate CPU = (?P<seconds>[0-9]+[.][0-9]+) seconds", line
            )
            if match:
                entry["replicate_cpu_seconds"] = float(match.groupdict()["seconds"])
                continue

            if line.startswith("Unit style"):
                entry["unit_style"] = line.split(":")[-1].strip()
                continue

            if line.startswith("Time step"):
                entry["time_step"] = float(line.split(":")[-1].strip())
                continue

            match = re.search(
                "Per MPI rank memory allocation (min/avg/max) = (?P<min_mpi_rank_memory_allocation_mb>[0-9]+[.][0-9]+) [|] (?P<avg_mpi_rank_memory_allocation_mb>[0-9]+[.][0-9]+) [|] (?P<max_mpi_rank_memory_allocation_mb>[0-9]+[.][0-9]+) Mbytes",
                line,
            )
            if match:
                [entry.update({k: int(v)}) for k, v in match.groupdict().items()]
                continue

            # If we find the embedded table with steps
            if line.startswith("Step"):
                header = [x.strip() for x in line.split(" ") if x.strip()]
                matrix = []
                line = lines.pop(0)
                while not line.startswith("Loop"):
                    matrix.append(
                        [float(x.strip()) for x in line.split(" ") if x.strip()]
                    )
                    line = lines.pop(0)
                entry["steps"] = pandas.DataFrame(matrix, columns=header).to_csv()

                # Here we have the loop line
                match = re.search(
                    "Loop time of (?P<loop_time>[0-9]+[.][0-9]+) on (?P<loop_procs>[0-9]+) procs for (?P<loop_steps>[0-9]+) steps with (?P<loop_atoms>[0-9]+) atoms",
                    line,
                )
                if match:
                    values = match.groupdict()
                    entry.update(
                        {
                            "loop_time": float(values["loop_time"]),
                            "loop_procs": int(values["loop_procs"]),
                            "loop_atoms": int(values["loop_atoms"]),
                        }
                    )
                    continue

            match = re.search(
                "Performance: (?P<performance_ns_per_day>[0-9]+[.][0-9]+) ns/day, (?P<performance_hours_per_ns>[0-9]+[.][0-9]+) hours/ns, (?P<timesteps_per_second>[0-9]+[.][0-9]+) timesteps/s",
                line,
            )
            if match:
                [entry.update({k: float(v)}) for k, v in match.groupdict().items()]
                continue

            # If we find the embedded table with times
            if line.startswith("Section"):
                header = [x.strip() for x in line.split("|") if x.strip()]

                # Line with full ----------------------
                lines.pop(0)
                matrix = pandas.DataFrame(columns=header[1:])
                line = lines.pop(0)
                while line.strip():
                    parts = [x.strip() for x in line.split("|")]
                    idx, rest = parts[0], parts[1:]
                    matrix.loc[idx, :] = rest
                    line = lines.pop(0)

                entry["times"] = matrix.to_csv()
                continue

        results[file] = entry
    return results


# TODO PLOTTING and savings results


def get_parser():
    """
    Return process laamps output parser.

    We require an output directory, optionally a plot name and slot/pod boolean.
    """
    parser = argparse.ArgumentParser(description="Process LAMMPS outputs")
    parser.add_argument("data_dir", help="data directory root")
    parser.add_argument(
        "-p",
        "--plotname",
        default="lammps",
        help="base name for plot output files",
    )
    parser.add_argument(
        "--spp",
        "--slot_per_pod",
        required=False,
        action="store_true",
        help="generate slot per pod plot",
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    results = gather_outputs(args.data_dir)
    # Save temporary results for online viewing until we know what to plot
    with open("results.json", "w") as fd:
        fd.write(json.dumps(results, indent=4))


if __name__ == "__main__":
    main()
