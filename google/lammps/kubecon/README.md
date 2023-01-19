# Lammps Experiments for Kubecon

In this set of experiments we will run the Flux Operator on Amazon Cloud on a size 32 (node)
cluster, and varing the size of the Flux Operator Mini Cluster between 4,8,16, and 32 for 20
times each.

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

Or (for testing) to bring up just the first cluster and then manually apply:

```bash
$ flux-cloud up
$ flux-cloud apply
$ flux-cloud down
```

By default, results will be written to a [./data](data) directory, but you can customize this with `--outdir`.

## Results

We have provided  a [process_lammps.py](process_lammps.py) script (under development) you can
use against the output data directory (and output files) to visualize the results.

**Note** we have not updated this yet for the multiple commands, e.g., if you
run more than one job it would need to be considered in a distribution, etc. 
There likely will be an error if you run it - we will update this script when we do the larger runs!

```bash
$ python -m venv env 
$ source env/bin/activate
$ pip install -r requirements.txt
```

Next, run the script targeting the data directory generated:

```bash
$ python process_lammps.py ./data
```
