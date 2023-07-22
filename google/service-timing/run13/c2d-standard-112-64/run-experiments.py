#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import time

here = os.path.abspath(os.path.dirname(__file__))

# Basic submit and monitor / saving of logs for multiple jobs
# Submit 10 times, each on 2 nodes
# cd /opt/lammps/examples/reaxff/HNS
# python run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 2 --times 10 -N 2 lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite --outdir /home/scohat1/etc --identifier lammps

# Make sure we can connect to the handle
try:
    import flux
    import flux.job

    handle = flux.Flux()

except ImportError:
    sys.exit("Cannot import flux, is the broker running?")


def get_parser():
    parser = argparse.ArgumentParser(
        description="Flux Basic Experiment Runner",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-id", "--identifier", help="Identifier for the run", default="lammps"
    )
    parser.add_argument("--workdir", help="working directory")
    parser.add_argument(
        "--outdir",
        help="output directory for logs, etc.",
        default=os.path.join(here, "data"),
    )
    parser.add_argument("-N", help="number of nodes", type=int, default=1)
    parser.add_argument(
        "--sleep", help="sleep seconds waiting for jobs", type=int, default=10
    )
    parser.add_argument("--tasks", help="number of tasks", type=int, default=1)
    parser.add_argument(
        "--times", help="Number of times to run experiment command", type=int
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print example command and exit",
    )
    return parser


def get_info(jobid):
    """
    Get details for a job
    """
    jobid = flux.job.JobID(jobid)
    payload = {"id": jobid, "attrs": ["all"]}
    rpc = flux.job.list.JobListIdRPC(handle, "job-list.list-id", payload)
    try:
        jobinfo = rpc.get()

    # The job does not exist!
    except FileNotFoundError:
        return None

    jobinfo = jobinfo["job"]

    # User friendly string from integer
    state = jobinfo["state"]
    jobinfo["state"] = flux.job.info.statetostr(state)

    # Get job info to add to result
    info = rpc.get_jobinfo()
    jobinfo["nnodes"] = info._nnodes
    jobinfo["result"] = info.result
    jobinfo["returncode"] = info.returncode
    jobinfo["runtime"] = info.runtime
    jobinfo["priority"] = info._priority
    jobinfo["waitstatus"] = info._waitstatus
    jobinfo["nodelist"] = info._nodelist
    jobinfo["nodelist"] = info._nodelist
    jobinfo["exception"] = info._exception.__dict__

    # Only appears after finished?
    if "duration" not in jobinfo:
        jobinfo["duration"] = ""
    return jobinfo


def main():
    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, command = parser.parse_known_args()

    # Show args to the user
    print("         N: %s" % args.N)
    print("     times: %s" % args.times)
    print("     sleep: %s" % args.sleep)
    print("    outdir: %s" % args.outdir)
    print("     tasks: %s" % args.tasks)
    print("   command: %s" % " ".join(command))
    print("   workdir: %s" % args.workdir)
    print("   dry-run: %s" % args.dry_run)
    print("identifier: %s" % args.identifier)

    # Ensure output directory exists
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    def get_job_prefix(i):
        identifier = f"{args.identifier}-{i}"
        return os.path.join(args.outdir, identifier)

    # Hard code options for all setups
    flux_options = [
        "-ompi=openmpi@5",
        "-c",
        "1",
        "-o",
        "cpu-affinity=per-task",
        "--watch",
        "-vvv",
    ]

    # Submit all jobs
    jobs = []
    for i in range(args.times):
        prefix = get_job_prefix(i)
        outfile = f"{prefix}.log"

        flux_command = (
            [
                "flux",
                "submit",
                "-N",
                str(args.N),
                "-n",
                str(args.tasks),
                "--output",
                outfile,
                "--error",
                outfile,
            ]
            + flux_options
            + command
        )

        # If doing a dry run, stop here
        print(" ".join(flux_command))
        if args.dry_run:
            continue

        jobid = subprocess.check_output(flux_command)
        jobid = jobid.decode("utf-8").strip()
        count = i + 1
        print(f"Submit {jobid}: {count} of {args.times}")
        jobs.append(jobid)


    # At this point all jobs are submit, and each should use all resources
    # so we *should* be running one at a time. Now we can wait for each to save output, etc.
    # Wait for futures
    print("\n⭐️ Waiting for jobs to finish...")
    for i, jobid in enumerate(jobs):
        state = "RUN"
        while state == "RUN":
            info = get_info(jobid)
            if info and info["state"] == "INACTIVE":
                state = info["state"]
                print(
                    f"No longer waiting on job {jobid}, FINISHED {info['returncode']}!"
                )
                break
            else:
                print(f"    Still waiting on job {jobid}, has state {info['state']}")
                time.sleep(args.sleep)

        # When we get here, save all the metadata
        prefix = get_job_prefix(i)
        outfile = f"{prefix}-info.json"
        with open(outfile, "w") as fd:
            fd.write(json.dumps(info, indent=4))
    print("Jobs are complete, goodbye! 👋️")

if __name__ == "__main__":
    main()
