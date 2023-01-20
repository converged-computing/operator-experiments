# Lammps on Google Kubernetes Engine

In this set of experiments we will run the Flux Operator on Google Cloud at size N=4.

## Pre-requisites

You should first [install gcloud](https://cloud.google.com/sdk/docs/quickstarts)
and ensure you are logged in and have kubectl installed:

```bash
$ gcloud auth login
```

Depending on your install, you can either install with gcloud:

```bash
$ gcloud components install kubectl
```

or just [on your own](https://kubernetes.io/docs/tasks/tools/). In addition,
we will be using [Flux Cloud](https://github.com/converged-computing/flux-cloud) 
to run the Operator on Google Cloud Kubernetes engine.

```bash
$ pip install flux-cloud
```

Note that we ran this on flux-cloud==0.0.13.

## Run Experiments

Each experiment here is defined by the matrix and variables in [experiments.yaml](experiment.yaml) 
and we use a minicluster-template.yaml defined by flux cloud, meaning each job is required to minimally
have an image. You can read the documentation for flux-cloud to understand the variables available.
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