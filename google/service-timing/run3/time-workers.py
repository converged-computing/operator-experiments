#!/usr/bin/env python3
# coding: utf-8

# This is an example of creating a Lammps cluster using the native API models
# directly (and not using the client.FluxOperator or client.FluxMiniCluster classes)

import statistics
from kubernetes import client, config
from fluxoperator.client import FluxMiniCluster
import datetime
import copy
import time
import json
import os
import sys

# prepare to write output files
here = os.path.abspath(os.path.dirname(__file__))
outdir = os.path.join(here, "data", "telnet")
if not os.path.exists(outdir):
    os.makedirs(outdir)

# We want the worker pod to run this, so we can see when it connects to the broker (and is ready)
telnet_script = """

for i in `seq 1 30`; do
    echo $i
    date '+%s.%N'
    true | telnet flux-sample-0.flux-service.flux-operator.svc.cluster.local 8050 && break
    echo
    sleep 1
done

"""

# Here is our main container - the command doesn't matter because the nslookup check
# above will exit when it connects
container = {
    "image": "ghcr.io/rse-ops/nslookup:flux-sched-focal",
    "working_dir": "/home/flux/examples/reaxff/HNS",
    "command": "echo hello world",
    "flux_log_level": 7,
    "commands": {"worker_pre": telnet_script, "workerPre": telnet_script},
}

# Make sure your cluster or minikube is running
# and the operator is installed
config.load_kube_config()

crd_api = client.CustomObjectsApi()

# Interact with the Flux Operator Python SDK
mc = {
    # Note that when you enable a service pod, the indexed job can come up 3-4 seconds faster
    # it seems like a bug, unfortunatly
    "size": 4,
    "namespace": "flux-operator",
    "name": "flux-sample",
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

    # We will get 3 workers per run
    times = []
    
    # 21 times each, one extra so we can skip the first (pulling containers)
    for i in range(0, 21):
        print(f"TESTING iteration {i} with telnet")
        operator = FluxMiniCluster()
        start = time.time()
        operator.create(**minicluster, container=container)

        # This calls the underlying controller for the minicluster using kubernetes in Python
        for pod in operator.ctrl.get_pods(
            name=operator.name, namespace=operator.namespace
        ).items:
            # We don't care about the broker
            name = pod.metadata.name
            if name.startswith("flux-sample-0"):
                continue
            name_prefix = name.rsplit("-", 1)[0]
            outfile = os.path.join(outdir, f"telnet-{i}-{name_prefix}.log")
            lines = operator.ctrl.stream_output(
                outfile,
                name=operator.name,
                namespace=operator.namespace,
                stdout=stdout,
                timestamps=True,
                pod=name,
            )
            # This is the first attempt
            telnet_line = [x for x in lines if "telnet" in x]
            
            # Assume no telnet line means it connected first try
            if not telnet_line:
                times.append(0)
                continue

            telnet_line = telnet_line[0].split(' ')[0]

            # This is the first connection
            connected_line = [x for x in lines if "Connected to flux-sample-0" in x][0].split(' ')[0]
           
            # Rough estimate - removing milliseconds because it's hard to parse
            connect_time = datetime.datetime.strptime(connected_line.rsplit('.')[0], "%Y-%m-%dT%H:%M:%S")           
            telnet_time = datetime.datetime.strptime(telnet_line.rsplit('.')[0], "%Y-%m-%dT%H:%M:%S")           
            
            # Try to parse seconds / milliseconds
            seconds = (connect_time - telnet_time).seconds
            connected_time_ms = float("." + connected_line.split('.')[-1].strip('Z'))
            telnet_time_ms = float("." + telnet_line.split('.')[-1].strip('Z'))           
            times.append(seconds + (connected_time_ms - telnet_time_ms))

        print(times)
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


results_file = os.path.join(outdir, "telnet-times.json")
run_experiments(results_file, False, stdout=True)
