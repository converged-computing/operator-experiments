#!/usr/bin/env python3
# coding: utf-8

# This is an example of creating a Lammps cluster using the native API models
# directly (and not using the client.FluxOperator or client.FluxMiniCluster classes)

import statistics
from kubernetes import client, config
from fluxoperator.client import FluxMiniCluster
import argparse
import copy
import time
import json
import sys
import os

here = os.path.abspath(os.path.dirname(__file__))

# Here is our main container
container = {
    "image": "ghcr.io/rse-ops/lammps-mpich:tag-mamba@sha256:fabf2e33a20589532a89e9cf0a6c716d754ffa3ba0018e312428155f961bfdbd",
    "working_dir": "/home/flux/examples/reaxff/HNS",
    "command": "lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite",
    "flux_log_level": 7,
    "resources": {
        "limits": {"memory": "28G"},  # We actually have 35.
        "requests": {"memory": "28G"},
    },
    "environment": {
        "LD_LIBRARY_PATH": "/opt/conda/lib",
        "PYTHONPATH": "/opt/conda/lib/python3.10/site-packages",
    },
}

# Make sure your cluster or minikube is running
# and the operator is installed
config.load_kube_config()

crd_api = client.CustomObjectsApi()

# Note that you might want to do this first for minikube
# minikube ssh docker pull ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0

# flux options flags
flags = "-ompi=openmpi@5 -c 1 -o cpu-affinity=per-task"

# Interact with the Flux Operator Python SDK
mc = {
    "size": 8,
    "tasks": 32,  # 4 x 8
    "namespace": "flux-operator",
    # This starts the flux broker without a command (interactive)
    # It will run indefinitely until you delete the CRD
    "interactive": False,
    "name": "flux-sample",
    "logging": {"zeromq": True, "quiet": False, "strict": False},
    "flux": {
        "wrap": "strace,-e,network,-tt",
        "optionFlags": flags,
        "option_flags": flags,
        "connect_timeout": "5s",  # This is the default
    },
}


def get_parser():
    parser = argparse.ArgumentParser(
        description="Experiment GKE Runner",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("tag", help="Tag for output directory (subfolder)")
    parser.add_argument(
        "-i",
        "--iter",
        dest="iter",
        help="Number of iterations to run.",
        default=20,
        type=int,
    )
    parser.add_argument(
        "--outdir", help="Output directory", default=os.path.join(here, "data")
    )
    parser.add_argument(
        "--pull",
        help="Do a preliminary pull of the container",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--service",
        help="Run with a separate, one-off service",
        default=False,
        action="store_true",
    )
    return parser


def main():
    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, _ = parser.parse_known_args()

    # prepare to write output files
    outdir = os.path.join(args.outdir, args.tag)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    with_stdout = False
    output_file = "lammps-no-services.json"
    if args.service:
        output_file = "lammps-with-services.json"

    run_experiments(
        outdir,
        os.path.join(outdir, output_file),
        args.service,
        with_stdout,
        args.pull,
        iterations=args.iter,
    )


def run_experiments(
    outdir,
    results_file=None,
    with_services=False,
    stdout=False,
    do_pull=False,
    iterations=10,
):
    """
    Shared script to run experiments, so we can try across many different cases
    """
    minicluster = copy.deepcopy(mc)
    log_slug = ""
    if with_services:
        log_slug = "-services"
        minicluster["services"] = [
            {
                "image": "nginx",
                "name": "nginx",
                "ports": [80],
            }
        ]

    # If we are pulling for the first time
    if do_pull:
        print("Pulling containers to nodes...")
        operator = FluxMiniCluster()
        operator.create(**minicluster, container=container)
        operator.delete()

    times = {}
    means = {}
    stds = {}

    def save_results():
        results = {"times": times, "means": means, "stds": stds}
        with open(results_file, "w") as fd:
            fd.write(json.dumps(results, indent=4))

    # Consistent timeouts
    slug = "5s"
    minicluster["flux"]["connect_timeout"] = slug

    # Be pedantic and lazy and save everything as we go
    times[slug] = []
    means[slug] = []
    stds[slug] = []

    log_final_slug = f"{slug}{log_slug}"
    for iter in range(0, iterations):
        print(f"TESTING {slug} iteration {iter}")
        try:
            operator = FluxMiniCluster()
            start = time.time()
            operator.create(**minicluster, container=container)

            # Ensure we keep it hanging until the job finishes - this is log for index 0
            outfile = os.path.join(
                outdir, f"lammps-{iter}-0-leader{log_final_slug}.log"
            )
            operator.stream_output(outfile, stdout=stdout, timestamps=True)
            end = time.time()
            runtime = end - start
            times[slug].append(runtime)
            print(
                f"Runtime for teeny LAMMPS {log_final_slug} iteration {iter} is {runtime} seconds"
            )

            # Save debug for remainder of pods
            for pod in operator.ctrl.get_pods(
                name=operator.name, namespace=operator.namespace
            ).items:
                # We don't care about the broker, and services container will hang forever
                name = pod.metadata.name
                if "flux-sample-0" in name or "-services" in name:
                    continue
                name_prefix = name.rsplit("-", 1)[0]
                outfile = os.path.join(
                    outdir, f"lammps-{iter}-{name_prefix}{log_final_slug}.log"
                )
                operator.ctrl.stream_output(
                    outfile,
                    name=operator.name,
                    namespace=operator.namespace,
                    stdout=stdout,
                    timestamps=True,
                    pod=name,
                )

            operator.delete()
            save_results()

        except:
            print(f"There was an issue with iteration {iter}")
            import IPython

            IPython.embed()

    print(json.dumps(times[slug]))
    means[slug] = statistics.mean(times[slug])
    stds[slug] = statistics.stdev(times[slug])
    print(f"Mean: {means[slug]}")
    print(f"Std: {stds[slug]}")

    print("\nFinal Results:")
    print(json.dumps(times))
    save_results()


if __name__ == "__main__":
    main()
