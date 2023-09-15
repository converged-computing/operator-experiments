# Automating OSU Scale

This small experiment will automate what we want to do for our larger experiments.
Each YAML in [crd](crd) represents a subset of experiments to run. Since networking
might be influenced by having more than one job on the cluster, we run them each once
at a time.

## OSU Benchmarks

Here is a testing (small) setup for a size 4 cluster (+2 nodes for operator controllers)

```bash
GOOGLE_PROJECT=myproject

# Add two nodes for jobset and metrics operator
gcloud container clusters create osu-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=6 \
    --machine-type=c2d-standard-2 \
    --enable-gvnic
```

Note that we will be using this configuration (130 nodes) is ~$12/hour (rounded up)

```bash
GOOGLE_PROJECT=myproject

# Add two nodes for jobset and metrics operator
gcloud container clusters create osu-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=130 \
    --machine-type=c2d-standard-2 \
    --enable-gvnic
```

Install JobSet

```bash
VERSION=v0.2.0
kubectl apply --server-side -f https://github.com/kubernetes-sigs/jobset/releases/download/$VERSION/manifests.yaml
```

Install the metrics operator. Here we keep the exact version and digest.

```bash
kubectl apply -f ./operator/metrics-operator.yaml
```

Save some metadata about the nodes:

```bash
kubectl get nodes -o json > nodes.json
```

Install the Metrics Operator SDK

```bash
pip install metricsoperator==0.0.18
```

Now we can automate with the script. Note that we target a directory of CRD, so you can target the actual (or tests).
Note that since test files are organized based on the number of iterations, we run each one separately (as opposed
to an entire directory).

```bash
# Run the test experiments
python run-experiment.py --out ./results --input ./crd/test/metrics-2.yaml --iter 2 --sleep 60
python run-experiment.py --out ./results --input ./crd/test/metrics-4.yaml --iter 2 --sleep 5
```

When you are done, clean up.

```bash
gcloud container clusters delete osu-cluster
```

Next time we will run the above, adjusted for adding our custom runs!
