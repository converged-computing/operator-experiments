#!/usr/bin/env python3
# coding: utf-8

# This is an example of creating a Lammps cluster using the native API models
# directly (and not using the client.FluxOperator or client.FluxMiniCluster classes)

import statistics
from kubernetes import client, config
from fluxoperator.client import FluxMiniCluster
import copy
import time
import json
import sys
import os

# Get tag (runtype)
if len(sys.argv) != 2:
    sys.exit("Please include the save tag!")
tag = sys.argv[1]

# prepare to write output files
here = os.path.abspath(os.path.dirname(__file__))
outdir = os.path.join(here, "data", tag)
if not os.path.exists(outdir):
    os.makedirs(outdir)

# Here is our main container
container = {
    "image": "ghcr.io/rse-ops/lammps-mpich:tag-mamba@sha256:fabf2e33a20589532a89e9cf0a6c716d754ffa3ba0018e312428155f961bfdbd",
    "working_dir": "/home/flux/examples/reaxff/HNS",
    "command": "lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite",
    "flux_log_level": 7,
    "resources": {"limits": {"cpu": 1}, "requests": {"cpu": 1}},
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
    # Note that when you enable a service pod, the indexed job can come up 3-4 seconds faster
    # it seems like a bug, unfortunatly
    "size": 4,
    "namespace": "flux-operator",
    "name": "flux-sample",
    "logging": {"zeromq": True},
    "flux": {
        "wrap": "strace,-e,network,-tt",
        "optionFlags": flags,
        "option_flags": flags,
        "connect_timeout": "5s",
    },
}


def run_experiments(
    results_file=None, with_services=False, stdout=False, do_pull=False
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

    # This will test timeouts for the connection between 0 and 10
    # Along with the case of not setting one
    # A time of zero will be unset (default to 30 seconds, long!)
    for timeout in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, None]:

        if timeout is None:
            slug = "no-timeout-set"
            minicluster["flux"]["connect_timeout"] = ""
        else:
            slug = f"{timeout}s"
            minicluster["flux"]["connect_timeout"] = slug

        # Be pedantic and lazy and save everything as we go
        times[slug] = []
        means[slug] = []
        stds[slug] = []

        log_final_slug = f"{slug}{log_slug}"
        # 20 times each
        for iter in range(0, 20):
            print(f"TESTING {slug} iteration {iter}")
            try:
                operator = FluxMiniCluster()
                start = time.time()
                operator.create(**minicluster, container=container)

                # Ensure we keep it hanging until the job finishes - this is log for index 0
                outfile = os.path.join(outdir, f"lammps-{iter}-0-leader{log_final_slug}.log")
                operator.stream_output(outfile, stdout=stdout, timestamps=True)
                end = time.time()
                runtime = end - start
                times[slug].append(runtime)
                print(f"Runtime for teeny LAMMPS {log_final_slug} iteration {iter} is {runtime} seconds")

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

            except:
                print(f"Issue with iteration {iter}")
                import IPython

                IPython.embed()

        print(json.dumps(times[slug]))
        means[slug] = statistics.mean(times[slug])
        stds[slug] = statistics.stdev(times[slug])
        print(f"Mean: {means[slug]}")
        print(f"Std: {stds[slug]}")

    print("\nFinal Results:")
    print(json.dumps(times))
    print(f"Means: {means}")
    print(f"Stds: {stds}")
    results = {"times": times, "means": means, "stds": stds}
    with open(results_file, "w") as fd:
        fd.write(json.dumps(results, indent=4))


# To run these I commented each out separately, just so I'd have two script runs
# There is some error in kubernetes with too many open files I need to look into
# but this seems to get around it
with_stdout = False
run_experiments(os.path.join(outdir, "lammps-no-services.json"), False, with_stdout, True)
#run_experiments(
#    os.path.join(outdir, "lammps-with-services.json"), True, with_stdout, False
#)
