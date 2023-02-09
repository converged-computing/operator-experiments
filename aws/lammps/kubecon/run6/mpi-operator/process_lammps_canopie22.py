#!/usr/bin/env python3

# This script was modified from the original to not plot, but just save
# results for another script to plot. The original is here:
# https://github.com/flux-framework/flux-k8s/blob/canopie22-artifacts/canopie22-artifacts/lammps/process_lammps.py

# Usage
# python process_lammps_canopie22.py --output-dir ./logs
# python process_lammps_canopie22.py # defaults to ./logs

import os
import argparse
import re
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def timestr2seconds(timestr):
    """
    Given a timestring in two formats, return seconds (float).
    """
    # Minutes and seconds, MM:SS.mm
    if timestr.count(":") == 1:
        minutes, seconds = timestr.split(":")
        return (int(minutes) * 60) + float(seconds)

    # hours, minutes, seconds HH:MM:SS.mm
    elif timestr.count(":") == 2:
        hours, minutes, seconds = timestr.split(":")
        return (int(hours) * 360) + (int(minutes) * 60) + float(seconds)
    raise ValueError(f"Unrecognized time format {timestr}")


def gather_outputs(outdir):
    results = {
        "scheduler": [],
        "ranks": [],
        "startup_time": [],
        "runtime": [],
        "lammps_time": [],
        "end_to_end_time": [],
        "FOM": [],
        "timesteps/s": [],
        "max_ppn": [],
        "real": [],
        "zones": [],
        "pods": [],
    }

    for file in os.listdir(outdir):
        if file.startswith("lammps") and file.endswith(".out"):
            with open(f"{outdir}/{file}", "r") as f:
                lines = f.readlines()
            ppn_max = 1
            real_t = None
            pods = None
            total_wall_time = None
            zones = set()
            for line in lines:
                if "for scheduler" in line:
                    sched = line.strip().split(" ")[-1]
                elif line.startswith("Ranks:"):
                    try:
                        nranks = int(line.strip().replace(",", "").split(" ")[1])
                    except ValueError:
                        nranks = line.strip().replace(",", "").split(" ")[1]
                    pods = int(line.split('pods:', 1)[-1].strip().split(',')[0])
                elif line.startswith("Performance:"):
                    timesteps_s = float(line.strip().split(" ")[-2])
                elif line.startswith("Loop time of"):
                    natoms = int(line.strip().split(" ")[-2])
                elif line.startswith("real"):
                    tmp = line.strip().split(" ")[-1]
                    try:
                        real_t = float(tmp)
                    except:
                        try:
                            real_t = float(re.search("m(.+?)s", tmp).group(1))
                        except AttributeError:
                            print("Unix runtime not found in substring")
                            raise
                elif line.startswith('Total wall time'):
                    rawtime = line.split(":", 1)[-1].strip()
                    total_wall_time = timestr2seconds(rawtime)

                elif line.startswith("MPIJob startup time for job"):
                    startup = float(line.strip().split(" ")[-2])
                elif line.startswith("MPIJob runtime for job"):
                    runtime = float(line.strip().split(" ")[-2])
                elif line.startswith("MPIJob end-to-end"):
                    e_to_e = float(line.strip().split(" ")[-2])
                elif "ran" and "pods in zone" in line:
                    pod_tmp = int(line.strip().split(" ")[2])
                    ppn_max = max([pod_tmp, ppn_max])
                    zones.add((line.strip().split(" ")[-1]))
            fom = timesteps_s * natoms
            results["FOM"].append(fom)
            results["real"].append(real_t)
            results["timesteps/s"].append(timesteps_s)
            results["scheduler"].append(sched)
            results["ranks"].append(nranks)
            results["startup_time"].append(startup)
            
            # Note that this value is incorrect!
            results["runtime"].append(runtime)
            results["end_to_end_time"].append(e_to_e)
            results["max_ppn"].append(ppn_max)
            results["zones"].append(len(zones))
            results["pods"].append(pods)
            results['lammps_time'].append(total_wall_time)

    return pd.DataFrame(data=results)

def main():
    parser = argparse.ArgumentParser(description="Process LAMMPS outputs")
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default="logs",
        help="directory with the experimental outputs",
    )
    args = parser.parse_args()
    output_entries = args.output_dir.split(",")
    df = pd.concat(gather_outputs(x) for x in output_entries)
    to_save = df.to_dict(orient="records")

    # This is the data file we need to compare with the Flux Operator
    with open('mpi_operator_results.json', 'w') as fd:
        fd.write(json.dumps(to_save, indent=4))


if __name__ == "__main__":
    main()
