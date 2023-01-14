# Lammps on Amazon Cloud

In this set of experiments we will run the Flux Operator on Amazon Cloud at size N=2
(the benchmarks require this) and multiple machine types.

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

### Setup SSH

You'll need an ssh key for EKS. Here is how to generate it:

```bash
ssh-keygen
# Ensure you enter the path to ~/.ssh/id_eks
```

This is used so you can ssh (connect) to your workers!

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

Then you can either run all at once:

```bash
$ flux-cloud run --force-cluster
```

Or (for testing) to bring up just the first cluster and then manually apply:

```bash
$ flux-cloud up
$ flux-cloud apply
$ flux-cloud down
```

or do the same for a targeted Kubernetes cluster:

```bash
$ flux-cloud up -e n1-standard-2-2
$ flux-cloud apply -e n1-standard-2-2
$ flux-cloud down -e n1-standard-2-2
```


The latter will either use a single experiment you've defined under `experiment` in your experiments.yaml file,
or select the first in your matrix (as we have here).

By default, results will be written to a [./data](data) directory, but you can customize this with `--outdir`.


## Results

We have provided  a [process_lammps.py](process_lammps.py) script (under development) you can
use against the output data directory (and output files) to visualize the results.
First, create an environment and install dependencies:

```bash
$ python -m venv env 
$ source env/bin/activate
$ pip install -r requirements.txt
```

Next, run the script targeting the data directory generated:

```bash
$ python process_lammps.py ./data
```