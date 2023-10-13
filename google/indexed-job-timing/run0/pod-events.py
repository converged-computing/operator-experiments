#!/usr/bin/env python3

# Launch jobs and watch for pods events. We only care about the ids and when they are created
# and then we can compare between cases. Since we have a small testing cluster here (kind)
# we will only do small tests.
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from functools import partial, update_wrapper

import yaml
from kubernetes import client as k8s
from kubernetes import config, watch

# Save data here
here = os.path.dirname(os.path.abspath(__file__))

# Create data output directory
data = os.path.join(here, "data")

# loading kubernetes config file and initializing client
# config.load_kube_config(config_file=args.kubeconfig)
config.load_kube_config()
k8s_client = k8s.CoreV1Api()


class timed:
    """
    Time the runtime of a function, add to times
    """

    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func

    def __get__(self, obj, objtype):
        return partial(self.__call__, obj)

    def __call__(self, cls, *args, **kwargs):
        name = self.func.__name__
        start = time.time()
        res = self.func(cls, *args, **kwargs)
        end = time.time()
        cls.times[name] = round(end - start, 3)
        return res


def recursive_find(base, pattern=None):
    """
    Find filenames that match a particular pattern, and yield them.
    """
    # We can identify modules by finding module.lua
    for root, folders, files in os.walk(base):
        for file in files:
            fullpath = os.path.abspath(os.path.join(root, file))

            if pattern and not re.search(pattern, fullpath):
                continue
            yield fullpath


def write_json(obj, path):
    """
    write json to file
    """
    with open(path, "w") as fd:
        fd.write(json.dumps(obj, indent=4))


def get_parser():
    parser = argparse.ArgumentParser(
        description="Pod Event Watcher",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--outdir", help="Path for the experimental results", default=data
    )
    parser.add_argument(
        "--size", help="Number of pods for indexed job or other", type=int
    )
    parser.add_argument("--idx", help="Index for experiment run")
    parser.add_argument(
        "--namespace",
        help="Kubernetes namespace",
        default="default",
    )
    parser.add_argument("input", help="Input directory for the experiment")
    return parser


def datetime_utcnow_str():
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_file(filename):
    with open(filename, "r") as file:
        content = file.read()
    return content


def read_yaml(filename):
    """
    Read yaml into dict (not used)
    """
    with open(filename, "r") as file:
        configuration = yaml.safe_load(file)
    return configuration


class Experiment:
    def __init__(self, yaml_file, outdir, size, idx=None):
        self.yaml_file = os.path.abspath(yaml_file)
        # Only read the first to get namespace, etc.
        self.raw = read_file(self.yaml_file)
        self.spec = yaml.safe_load(self.raw.split("---", 1)[0])
        self.times = {}
        self.events = {}
        self.size = size
        self.idx = idx
        self.setup(outdir, idx)

    def setup(self, outdir, idx):
        """
        Setup the output directory and set the experiment name
        """
        experiment_name = os.path.basename(self.yaml_file).split(".", 1)[0]
        if idx:
            experiment_name = f"{experiment_name}-{idx}"
        self.outdir = os.path.join(outdir, str(self.size), experiment_name)
        if not os.path.exists(self.outdir):
            print(f"📁️ Creating output directory {self.outdir}")
            os.makedirs(self.outdir)
        self.experiment_name = experiment_name

    def __str__(self):
        return os.path.basename(self.yaml_file).split(".", 1)[0]

    def __repr__(self):
        return str(self) + ".Experiment"

    def create(self):
        # Don't wait for finish so we see in events
        os.system(f"kubectl apply -f {self.yaml_file} &")

    def delete(self):
        # Don't wait for finish so we see in events
        os.system(f"kubectl delete -f {self.yaml_file} &")

    @property
    def group(self):
        return self.spec["apiVersion"].split("/", 2)[0]

    @property
    def version(self):
        return self.spec["apiVersion"].split("/", 2)[1]

    @property
    def kind(self):
        return self.spec["kind"].lower()

    @property
    def plural(self):
        return self.kind + "s"

    @property
    def namespace(self):
        return self.spec["metadata"].get("namespace") or "default"

    @property
    def name(self):
        return self.spec["metadata"]["name"]

    def save(self):
        """
        Save data to file
        """
        outfile = os.path.join(self.outdir, "events.json")
        print(f"Saving result for {self} to {outfile}")
        result = {
            "events": self.events,
            "times": self.times,
            "size": self.size,
            "spec": self.spec,
            "iteration": self.idx,
            "experiment": self.experiment_name,
        }
        write_json(result, outfile)

    @timed
    def watch_create(self):
        """
        Watch creation events
        """
        events = {}
        pods_done = set()
        watcher = watch.Watch()
        for event in watcher.stream(
            func=k8s_client.list_namespaced_pod, namespace=self.namespace
        ):
            pod_name = event["raw_object"]["metadata"]["name"]
            if pod_name not in events:
                events[pod_name] = []

            # we do not need object and does not serialize
            del event["object"]

            event_type = event["type"]
            print(f"Create event for pod {pod_name} 🫛  {event_type}")
            events[pod_name].append(
                {"event": event, "timestamp": datetime_utcnow_str()}
            )
            if is_creation_done(event):
                pods_done.add(pod_name)

            if len(pods_done) == self.size:
                print(f"Create events for {pod_name} are done")
                break

        self.events["create"] = events

    @timed
    def watch_delete(self):
        """
        Watch deletion events
        """
        events = {}
        watcher = watch.Watch()
        pods_deleted = set()

        # This should break when pods are deleted (no events)
        for event in watcher.stream(
            func=k8s_client.list_namespaced_pod, namespace=self.namespace
        ):
            # we do not need object and does not serialize
            del event["object"]

            pod_name = event["raw_object"]["metadata"]["name"]
            if pod_name not in events:
                events[pod_name] = []

            event_type = event["type"]
            print(f"Delete event for pod {pod_name} 🫛  {event_type}")
            events[pod_name].append(
                {"event": event, "timestamp": datetime_utcnow_str()}
            )
            if event_type == "DELETED":
                pods_deleted.add(pod_name)
            if len(pods_deleted) == self.size:
                break

        self.events["delete"] = events


def is_creation_done(event):
    """
    Determine if creation is done based on all statuses being true
    and the pod is Running. Specifically we need to find:

    phase: Running:
    conditions:
      Initialized: True
      Ready: True
      ContainersReady: True
      PodSCheduled: True
    """
    phase = event["raw_object"]["status"]["phase"].lower()
    conditions = event["raw_object"]["status"].get("conditions", [])
    return (
        phase == "running"
        and all([x["status"] == "True" for x in conditions])
        and len(conditions) == 4
    )


def run_experiment(experiment_yaml, outdir, size, idx=None):
    """
    Run experiments to watch a pod. We assume the default namespace
    """
    # Time creation, if there are trivial differences (probably not)
    test = Experiment(experiment_yaml, size=size, idx=idx, outdir=outdir)
    test.create()

    # Create and watch until all are running and statuses all True
    test.watch_create()
    print(f"All pods for {test} are done creation.")
    test.delete()
    test.watch_delete()
    print(f"All pods for {test} are deleted")
    test.save()


def main():
    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, _ = parser.parse_known_args()

    if not args.size:
        sys.exit("Please indicate the number of pods with --size")
    if not os.path.exists(args.input):
        sys.exit(f"Input directory {args.input} does not exist.")
    if not os.listdir(args.input):
        sys.exit(f"Input directory {args.input} has no input files")

    # Run each experiment file separately
    for experiment_yaml in recursive_find(args.input, "[.](yml|yaml)$"):
        run_experiment(
            experiment_yaml, outdir=args.outdir, size=args.size, idx=args.idx
        )


if __name__ == "__main__":
    main()
