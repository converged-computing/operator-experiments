#!/usr/bin/env python3

import argparse
import copy
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime

from jinja2 import Template
from kubernetes import client, config, watch

here = os.path.dirname(os.path.abspath(__file__))

# Hard coded experiment templates
lammps_template = os.path.join(here, "crd", "lammps.yaml")

# Also hard code sizes, etc. for now. Don't feel like maintaining separate files
# This is for kind, and the lookup is based on the number of pods for the job (1 to max of 4)
# The name and scheduler are added by the script
# I'm doing all size 3 for testing
kind_config = [
    {"x": 2, "y": 2, "z": 2, "cpu_limit": 2, "tasks": 2, "size": 1},
]
six_config = [
    {"x": 2, "y": 2, "z": 2, "cpu_limit": 3, "tasks": 8, "size": 2},
    {"x": 2, "y": 2, "z": 2, "cpu_limit": 3, "tasks": 12, "size": 3},
    {"x": 2, "y": 2, "z": 2, "cpu_limit": 3, "tasks": 16, "size": 4},
]


# Pair up configs and named templates
configs = {
    "lammps-kind": {"config": kind_config, "template": lammps_template},
    "lammps-six": {"config": six_config, "template": lammps_template},
}

# This must work to continue
config.load_kube_config()
kube_client = client.CoreV1Api()

# Try using a global watcher
watcher = watch.Watch()


def write_file(content, filename):
    """
    Write content to file.
    """
    with open(filename, "w") as fd:
        fd.write(content)


def read_file(filename):
    """
    Read content from file
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def get_cluster_config(logfile, cpus, memory):
    """
    Get cluster node configuration and build
    the zone topology map.
    """
    cluster_nodes = kube_client.list_node()
    nodes = cluster_nodes.to_str()
    write_file(nodes, logfile)

    # Assemble topology that includes nodes, cpu, and memory
    node_topology = {"nodes": {}, "cpu": cpus, "mem": memory}
    for node in cluster_nodes.items:
        # Mock for local testing, this label won't be in a kind cluster
        label = "local"
        if "topology.kubernetes.io/zone" in node.metadata.labels:
            label = node.metadata.labels["topology.kubernetes.io/zone"]
        node_topology["nodes"][node.metadata.name] = label
    return node_topology


def submit_job(minicluster_yaml):
    """
    Create the job in Kubernetes.
    """
    fd, filename = tempfile.mkstemp(suffix=".yaml", prefix="minicluster-")
    os.remove(filename)
    os.close(fd)
    write_file(minicluster_yaml, filename)

    # Create the minicluster
    o, e = run_command(["kubectl", "apply", "-f", filename])
    os.remove(filename)


def run_command(command):
    """
    Call a command to subprocess, return output and error.
    """
    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    o, e = p.communicate()
    print(o)
    if p.returncode:
        print(e)
        raise RuntimeError(e)
    return o, e


def delete_minicluster(uid):
    """
    Delete the Minicluster, which includes an indexed job,
    config maps, and service.
    """
    # --wait=true is default, but I want to be explicit
    run_command(
        ["kubectl", "delete", "miniclusters.flux-framework.org", uid, "--wait=true"]
    )


def record_line(filename, status, content):
    """
    Record (write with append) one entry to a file.
    """
    with open(filename, "a") as f:
        f.write(f"\n===\n{status}: recorded-at: {datetime.utcnow()}\n{content}")


def show_logs(name):
    """
    Show lines from the log.

    This will error when the pod isn't ready yet.
    """
    lines = []
    for line in watcher.stream(
        kube_client.read_namespaced_pod_log,
        name=name,
        namespace="default",
    ):
        print(line)
        lines.append(line)
    return "\n".join(lines)


def get_pod_mapping(uid, pods, scheduler, node_topology):
    """
    Get the pod topology based on node assignment, format into
    string to save back to log.
    """
    mapping = f"Mapping for job {uid} for scheduler {scheduler}\n"
    mapping_dict = defaultdict(int)
    for pod in pods.items:
        mapping_dict[pod.spec.node_name] += 1
        mapping += f"{pod.metadata.name} --> {pod.spec.node_name}\n"
    for worker_name, count in mapping_dict.items():
        mapping += f"{worker_name} ran {str(count)} pods in zone "
        mapping += f"{node_topology['nodes'][worker_name]}\n"
    return mapping


def get_run_configuration(uid, meta, node_topology):
    """
    The run configuration is a json dump of metadata
    plus snippets of the node_topology.
    """
    rconfig = f"Run configuration for job {uid}:\n===\n"
    rconfig += json.dumps(meta, indent=4) + "\n====\n"
    rconfig += f"Launcher CPUs: {node_topology['cpu']}\n"
    rconfig += f"Launcher memory in GiB: {node_topology['mem']}\n"
    return rconfig


def get_logs(uid, meta, start_time, log_dir, node_topology):
    """
    Get the application mapping and performance logs
    """
    log_file = os.path.join(log_dir, f"{uid}.log")

    # scheduler is in meta->params or we assume default
    scheduler = meta["params"].get("scheduler") or "default"

    # Find pods for minicluster
    label = meta["params"]["name"]

    # Wait for pods
    # Wait for the leader pod to be running before listing
    while True:
        pods = kube_client.list_namespaced_pod(
            label_selector=f"app={label}", namespace="default"
        )
        # Phases here:
        phases = [x.status.phase for x in pods.items]
        is_running = all([p in ["Running", "Succeeded", "Failed"] for p in phases])
        if len(pods.items) == meta["params"]["size"] and is_running:
            break

    # And then the 0th index (leader) and the rest are workers (not used here)
    zero_index = f"{label}-0"
    leader = [x for x in pods.items if x.metadata.name.startswith(zero_index)][0]
    print(f"Found minicluster leader pod {leader.metadata.name} to watch 👀️")

    # Stream log until it completes (and we will get events after)
    print(f"Waiting to get log for {uid} from pod {leader.metadata.name}")
    while True:
        try:
            log = show_logs(leader.metadata.name)

            # If we hit the point where it's running but no logs...
            if not log:
                continue
            break
        except:
            continue

    # Record the log to our file
    record_line(log_file, "Output", log)
    for event in watcher.stream(
        func=kube_client.list_namespaced_pod,
        namespace="default",
        label_selector=f"app={label}",
        timeout_seconds=1,
    ):
        # We only care about the leader
        if event["object"].metadata.name != leader.metadata.name:
            continue

        # We need this dump for both Failed and Succeeded
        # And we stop the watcher and save pod events for both
        phase = event["object"].status.phase
        print(f"Leader {leader.metadata.name} is in phase {phase}")
        if phase in ["Failed", "Completed", "Succeeded"]:
            event_dump = event["object"].to_dict()
            record_line(log_file, phase, event_dump)

            # Save pod event logs
            event_logfile = log_file.rsplit(".", 1)[0] + "-events.log"
            save_pod_events(event_logfile, label, leader)

        if phase == "Failed":
            raise RuntimeError(f"Job {uid} Failed at: {datetime.utcnow()}")

        elif phase == "Succeeded":
            # We already have the launcher logs
            # Get the job topology information from all nodes
            mapping = get_pod_mapping(uid, pods, scheduler, node_topology)
            record_line(log_file, "Mapping", mapping)

            # Get and add the run configuration
            run_config = get_run_configuration(uid, meta, node_topology)
            record_line(log_file, "Config", run_config)

            # Note that I deleted the get_operator_logs function here, the Flux
            # operator logs don't have content of interest.


def process_error_handler(e):
    """
    A simple process that prints and raises the error.
    """
    print(e)
    raise e


def save_pod_events(events_file, label, leader):
    """
    Get events for a pod based on a label

    TODO: we aren't currently using this because it didn't reliably
    return events, need to look into why.
    """
    # These should be able to get them after the pod finishes
    # Do we need these events, want to compare with the ones below?
    # This gets pod events, and then events for the leader (scheduler too)
    pod_events = []
    for event in watcher.stream(
        kube_client.list_namespaced_event,
        "default",
        label_selector=f"app={label}",
        timeout_seconds=10,
    ):
        pod_events.append(event)
    print(f"Events for pod {label}: {len(pod_events)}")
    events_dump = json.dumps([x["raw_object"] for x in pod_events], indent=4)
    record_line(events_file, "PodEvents", events_dump)


def run(config_name, iters, node_topology, using_fluence, outdir):
    """
    Run the experiments for the input apps.

    This is going to basically launch a crapton of experiments to run, much more than the
    scheduler can handle at once, and then we will monitor what it does. This script needs
    to be run twice, once with fluence and one without (one with the default scheduler)
    """
    # If we are using fluence we need to add this to the Minicluster CRD to add to the Pod
    scheduler = "default"
    if using_fluence:
        scheduler = "fluence"

    # Read in the template once
    experiment = configs[config_name]
    cfgs = experiment["config"]
    template = Template(read_file(experiment["template"]))

    # Keep record of all specs across batches
    specs = {}

    # Make a directory for the logs
    log_dir = os.path.join(outdir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # TODO double check - in the CANOPIE 22 experiments, the pod group was defined with the
    # same name. Would we not need to have unique names, one per group? I will try unique first,
    # because the docs seem to imply assigning specific pods. Note that we need the podgroup
    # for fluence, but not the default scheduler.
    for i in range(iters):
        # Keep a record of the uids we submit for this batch
        batch = set()

        # Run 1 of each experiment size for lammps
        # note that we can change how we do this (random, etc)
        for cfg in cfgs:
            size = cfg["size"]

            # uid is the iteration, size, and scheduler
            uid = f"{scheduler}-iter-{i}-size-{size}"
            batch.add(uid)

            # name is just the size and iteration
            minicluster_name = f"lammps-{i}-size-{size}"

            # The flux service needs to be unique for the minicluster
            service_name = f"fs{i}{size}"

            print(f"Starting job {uid}: {cfg}")
            render = copy.deepcopy(cfg)
            render.update(
                {"name": minicluster_name, "size": size, "service_name": service_name}
            )

            # if using fluence we add the scheduler name and create a pod group
            if using_fluence:
                render["scheduler"] = scheduler
                render["pod_group"] = minicluster_name

            # TODO: what else do we want to save here?
            specs[uid] = {"params": render, "iter": i}

            # Generate and submit the template...
            minicluster_yaml = template.render(render)
            print(minicluster_yaml)
            start_time = datetime.utcnow()

            # This submits the job, doesn't do more than that (e.g., waiting)
            submit_job(minicluster_yaml)

        # END of size loop
        # Here we start an asynchronous process pool to monitor the sizes in parallel
        # This assumes a unit of operator is a group of lammps running at different sizes
        # Is that what we want?

        # This was for manual testing
        # for uid in batch:
        #    get_logs(uid, specs[uid], start_time, log_dir, node_topology)

        # TODO I don't use start_time here for anything, but rather I save all
        # metadata. We can more easily calculate things here too, let's discuss
        with multiprocessing.Pool(processes=len(batch)) as pool:
            results = []
            for uid in batch:
                results.append(
                    pool.apply_async(
                        get_logs,
                        args=(
                            uid,
                            specs[uid],
                            start_time,
                            log_dir,
                            node_topology,
                        ),
                        error_callback=process_error_handler,
                    )
                )
            [result.wait() for result in results]

        # Delete each at the end
        for uid in batch:
            name = specs[uid]["params"]["name"]
            delete_minicluster(name)

    # Stop the watcher just once
    watcher.stop()
    print(f"🧪️ Experiments are finished. See output in {outdir}")


def confirm_action(question):
    """
    Ask for confirmation of an action
    """
    response = input(question + " (yes/no)? ")
    while len(response) < 1 or response[0].lower().strip() not in "ynyesno":
        response = input("Please answer yes or no: ")
    if response[0].lower().strip() in "no":
        return False
    return True


def get_parser():
    parser = argparse.ArgumentParser(
        description="Run Kubernetes Scheduler Scaling Study"
    )
    parser.add_argument(
        "--fluence",
        action="store_true",
        help="Use fluence and not the default scheduler",
    )
    parser.add_argument(
        "--cpus",
        type=int,
        required=True,
        help="number of CPUs per worker node",
    )
    parser.add_argument(
        "--config-name",
        default="lammps-kind",
        help="config name to use (defaults to lammps-kind)",
    )
    parser.add_argument(
        "--memory",
        type=int,
        required=True,
        help="GiB memory per worker node",
    )
    parser.add_argument(
        "--iters",
        type=int,
        default=10,
        help="iterations to run per experiment (defaults to 10)",
    )
    parser.add_argument(
        "--outdir",
        default=os.path.join(here, "results"),
        help="output directory for results",
    )
    return parser


def main():
    parser = get_parser()
    args, _ = parser.parse_known_args()

    # Ensure our template directory and templates exist
    if not os.path.exists(lammps_template):
        sys.exit(f"{lammps_template} does not exist.")

    outdir = os.path.abspath(args.outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Ensure the config is known
    if args.config_name not in configs:
        sys.exit(f"{args.config_name} is not a known configuration")

    # Show parameters to the user
    print(f"▶️  Output directory: {outdir}")
    print(f"▶️   Memory per node: {args.memory}")
    print(f"▶️     CPUs per node: {args.cpus}")
    print(f"▶️     Using Fluence: {args.fluence}")
    print(f"▶️       Config name: {args.config_name}")
    print(f"▶️        Iterations: {args.iters}")

    if not confirm_action("Would you like to continue?"):
        sys.exit("Cancelled!")

    # Write the topology to this file
    topology_file = os.path.join(outdir, "topology.json")

    # Write cluster node configuration and return mapping
    node_topology = get_cluster_config(topology_file, args.cpus, args.memory)

    try:
        run(args.config_name, args.iters, node_topology, args.fluence, args.outdir)
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":
    main()