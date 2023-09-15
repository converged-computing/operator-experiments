# OSU Experiments

These are the official CRD experiments (we are ready!) We will generate data first,
save all metadata and logs, and then parse them after. Each YAML in [crd](crd) 
represents a subset of experiments to run. Since networking
might be influenced by having more than one job on the cluster, we run them each once
at a time.

*running this weekend*

## OSU Benchmarks

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

Install the Metrics Operator SDK. Version 19 has added support for custom (raw) log parsing.

```bash
pip install metricsoperator==0.0.19
```

Now we can automate with the script. Note that we target a directory of CRD, so you can target each combination
of size and iterations (which varies).

```bash
# Run the test experiments - pull to all 128 pods first
# Size 128 we don't attempt the size 1 runs (too long)
python run-experiment.py --out ./results --input ./crd/metrics-20x-128.yaml --iter 20 --sleep 60

# Size 64 we split into 20x and 1x for larger runs
python run-experiment.py --out ./results --input ./crd/metrics-20x-64.yaml --iter 20 --sleep 5
python run-experiment.py --out ./results --input ./crd/metrics-1x-64.yaml --iter 1 --sleep 5

# Size 32 is the same...
python run-experiment.py --out ./results --input ./crd/metrics-20x-32.yaml --iter 20 --sleep 5
python run-experiment.py --out ./results --input ./crd/metrics-1x-32.yaml --iter 1 --sleep 5

# Size 16 flips ibarrier into the 20x group
python run-experiment.py --out ./results --input ./crd/metrics-20x-16.yaml --iter 20 --sleep 5
python run-experiment.py --out ./results --input ./crd/metrics-1x-16.yaml --iter 1 --sleep 5

# Size 8 is the same...
python run-experiment.py --out ./results --input ./crd/metrics-20x-8.yaml --iter 20 --sleep 5
python run-experiment.py --out ./results --input ./crd/metrics-1x-8.yaml --iter 1 --sleep 5

# Size 4 is all for 20
python run-experiment.py --out ./results --input ./crd/metrics-20x-4.yaml --iter 20 --sleep 5
```

When you are done, clean up!

```bash
gcloud container clusters delete osu-cluster
```

Next time we will run the above, adjusted for adding our custom runs!
