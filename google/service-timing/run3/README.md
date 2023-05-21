# Service Timing

See [notes in run1](../run1) for full background. This experiment will bring
up the same cluster (in terms of GKE flags) and look at telnet from the worker.
This will help us to see if/when it is connecting to the main broker port.

### Setup

#### 1. Dependencies

You'll need the Python bindings and a virtual environment. We just are using Python to programatically submit (and time) the jobs.

```bash
$ python -m venv env
$ source env/bin/activate
$ pip install fluxoperator # this should be 0.0.24
$ pip install kubernetes   # I was using 26.1.0
```

#### 2. Create Cluster

We will use dataplane-2 per suggestion [in this comment](https://github.com/kubernetes/kubernetes/issues/117819#issuecomment-1550444235):

```bash
$ gcloud container clusters create flux-operator \
   --region=us-central1-a --project $GOOGLE_PROJECT \
   --machine-type n1-standard-2 --num-nodes=4 \
   --tags=flux-cluster  --enable-dataplane-v2

$ kubectl create namespace flux-operator
$ kubectl apply -f operator/flux-operator.yaml

$ python time-workers.py
$ gcloud container clusters delete flux-operator
```

#### 3. Results

**still running**
