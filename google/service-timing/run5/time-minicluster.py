#!/usr/bin/env python3
# coding: utf-8

# This is an example of creating a Lammps cluster using the native API models
# directly (and not using the client.FluxOperator or client.FluxMiniCluster classes)

import statistics
from kubernetes import client, config
from fluxoperator.client import FluxMiniCluster
import copy
import datetime
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
    "image": "ghcr.io/rse-ops/nslookup:flux-sched-focal",
    "command": "sleep 5",
    "flux_log_level": 7,
    "resources": {"limits": {"cpu": 1}, "requests": {"cpu": 1}},
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
    "size": 4,
    "namespace": "flux-operator",
    "name": "flux-sample",
    "logging": {"zeromq": True},
    # Let's remove the connect timeout
    # "flux": {"connect_timeout": "5s"},
    "flux": {"wrap": "strace,-e,network,-tt"},
}


def parse_timestamp_seconds_ms(ts1, ts2):
    """
    Get timestamp seconds and ms
    """
    # Rough estimate - removing milliseconds because it's hard to parse
    time1 = datetime.datetime.strptime(ts1.rsplit(".")[0], "%Y-%m-%dT%H:%M:%S")
    time2 = datetime.datetime.strptime(ts2.rsplit(".")[0], "%Y-%m-%dT%H:%M:%S")

    # Try to parse seconds / milliseconds
    seconds = (time2 - time1).seconds
    time1_ms = float("." + ts1.split(".")[-1].strip("Z"))
    time2_ms = float("." + ts2.split(".")[-1].strip("Z"))
    return seconds + (time2_ms - time1_ms)


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

    # 21 times each
    for i in range(0, 20):
        print(f"TESTING iteration {i}")
        operator = FluxMiniCluster()
        operator.create(**minicluster, container=container)

        for pod in operator.ctrl.get_pods(
            name=operator.name, namespace=operator.namespace
        ).items:
            # We don't care about the broker
            name = pod.metadata.name
            name_prefix = name.rsplit("-", 1)[0]
            outfile = os.path.join(outdir, f"sleep-{i}-{name_prefix}.log")
            lines = operator.ctrl.stream_output(
                outfile,
                name=operator.name,
                namespace=operator.namespace,
                stdout=stdout,
                timestamps=True,
                pod=name,
            )
            if "flux-sample-0" in name:
                flux_submit = [x for x in lines if "flux start" in x][0].split(" ")[0]
                flux_exit = [x for x in lines if "rc2-success" in x][0].split(" ")[0]

                # Subtract 5 seconds for sleep to just get flux
                seconds = parse_timestamp_seconds_ms(flux_submit, flux_exit) - 5
                times.append(seconds)
        operator.delete()

    print("\nFinal Results:")
    print(json.dumps(times))
    results = {"times": times}
    with open(results_file, "w") as fd:
        fd.write(json.dumps(results, indent=4))


with_stdout = False
run_experiments(os.path.join(outdir, "flux-start-times.json"), False, with_stdout)
