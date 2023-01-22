# Lammps Experiments for Kubecon

In this set of experiments we will run the Flux Operator on Amazon Cloud on a size 64 (node)
cluster, and varing the size of the Flux Operator Mini Cluster between 4,8,16,32 and 64 for 20
times each. A few notes:

 - We run from largest down to smallest
 - The first run (64) has 21 runs since the first will pull containers (and needs to be thrown away)
 - The original experiments to compare to the MPI operator had extra mpirun flags that we determined the first and last cancel each other out, and the second we cannot currently support through Flux.
   - `--map-by numa`
   - `--rank-by core`
   - `--bind-to none`
 - We were not able to build the container on the same machine running the job, so it is not optimized for it.   


## Experiments

 - [run1](run1) was done with flux-cloud 0.1.12 that didn't ensure the pod space was cleaned up before launching the next, and the operator didn't have support for capturing flux start times.
 - [run2](run2) was done with flux-cloud 0.1.13 with this additional check, and the operator with support for logging.timed. The CRDs will not work if swapped between the two.


## Pre-requisites

You should first [install eksctrl](https://github.com/weaveworks/eksctl) and make sure you have access to an AWS cloud (e.g.,
with credentials or similar in your environment). E.g.,:

```bash
export AWS_ACCESS_KEY_ID=xxxxxxxxxxxxxxxxxxx
export AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export AWS_SESSION_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The last session token may not be required depending on your setup.
We assume you also have [kubectl](https://kubernetes.io/docs/tasks/tools/).

### Cloud

we will be using [Flux Cloud](https://github.com/converged-computing/flux-cloud) 
to run the Operator on Google Cloud Kubernetes engine.

```bash
$ pip install flux-cloud 
```

Ensure that aws is either your default cloud (the `default_cloud` in your settings.yml)
or you specify it with `--cloud` when you do run.


## Run Experiments

Each experiment here is defined by the matrix and variables in [experiments.yaml](experiment.yaml) that is used to
populate a [minicluster-template.yaml](minicluster-template.yaml) and launch a Kubernetes cluster.
You can read the documentation for flux-cloud to understand the variables available.
This tutorial assumes you have flux-cloud installed and configured. See all unique Kubernetes clusters
we will run the jobs on:

```bash
$ flux-cloud list
```

It's recommended for the below commands to use `--debug` if this is your first
time to see the configs generated (e.g., `flux-cloud --debug run`. 
To run all at once (only recommended for headless):

```bash
$ flux-cloud run --force-cluster
```

Or (for more careful application) we did each step separately:

```bash
$ flux-cloud --debug up --cloud aws
$ flux-cloud --debug apply --cloud aws
$ flux-cloud --debug down --cloud aws
```

By default, results will be written to a `data` directory within each folder, and within that
folder are organized subdirectories with logs, and a single `.script` directory for each size
with all configs and scripts that are used. 
