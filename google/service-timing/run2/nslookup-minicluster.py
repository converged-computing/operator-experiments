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
import os
import sys

if len(sys.argv) != 2:
    sys.exit("Please include a tag as the only argument")
tag = sys.argv[1]

# prepare to write output files
here = os.path.abspath(os.path.dirname(__file__))
outdir = os.path.join(here, "data", "nslookup", tag)
if not os.path.exists(outdir):
    os.makedirs(outdir)

nslookup_script = """

while true; do
    nslookup -timeout=1 lammps-0.flux-service.flux-operator.svc.cluster.local && exit 0 || echo "Server is not ready"
done

"""

# Here is our main container - the command doesn't matter because the nslookup check
# above will exit when it connects
container = {
    "image": "ghcr.io/rse-ops/nslookup:flux-sched-focal",
    "working_dir": "/home/flux/examples/reaxff/HNS",
    "command": "lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite",
    "flux_log_level": 7,
    "commands": {"pre": nslookup_script},
}

# Make sure your cluster or minikube is running
# and the operator is installed
config.load_kube_config()

crd_api = client.CustomObjectsApi()

# Note that you might want to do this first for minikube
# minikube ssh docker pull ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0

# Interact with the Flux Operator Python SDK
mc = {
    # Note that when you enable a service pod, the indexed job can come up 3-4 seconds faster
    # it seems like a bug, unfortunatly
    "size": 2,
    "namespace": "flux-operator",
    "name": "lammps",
    "logging": {"zeromq": True},
    # Set a reasonable timeout across
    "flux": {"connect_timeout": "5s"},
}


def run_experiments(results_file=None, with_services=False, stdout=False):
    """
    Shared script to run experiments, so we can try across many different cases
    """
    minicluster = copy.deepcopy(mc)
    if with_services:
        minicluster["services"] = [
            {
                "image": "nginx",
                "name": "nginx",
                "ports": [80],
            }
        ]

    times = []

    # 21 times each, one extra so we can skip the first (pulling containers)
    for i in range(0, 21):
        print(f"TESTING iteration {i} with nslookup")
        operator = FluxMiniCluster()
        start = time.time()
        operator.create(**minicluster, container=container)

        # Get the output from the operator
        outfile = os.path.join(outdir, f"nslookup-{i}.log")
        lines = operator.stream_output(outfile, stdout=stdout, timestamps=True)
        end = time.time()
        runtime = end - start
        times.append(runtime)
        print(f"Runtime for nslookup iteration {i} is {runtime} seconds")
        operator.delete()

    print("\nFinal Results:")
    print(json.dumps(times))
    mean = statistics.mean(times)
    std = statistics.stdev(times)
    print(f"Mean: {mean}")
    print(f"Std: {std}")

    results = {"times": times, "mean": mean, "std": std}
    with open(results_file, "w") as fd:
        fd.write(json.dumps(results, indent=4))


# This will run nslookup with and without the extra service pod.
# It shouldn't make a difference, but I suspect it will.
with_stdout = True
results_file = os.path.join(outdir, "nslookup-times-no-service.json")
run_experiments(results_file, False, with_stdout)
