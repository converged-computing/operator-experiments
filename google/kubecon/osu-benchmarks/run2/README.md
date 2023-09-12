# Developing OSU Scale

We now want to bring up a larger cluster (size 128) of a smaller instance, and test
scatter/gather for collective benchmarks and the smaller ones.

## OSU Benchmarks

Note this configuration (128 nodes) is $11.62/hour.

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

And the operator (I installed a development version):

```bash
make test-deploy-recreate
```

Save some metadata!

```bash
kubectl get nodes -o json > nodes.json
```

Let 'er run!

```bash
kubectl apply -f metrics-128.yaml 
# Watch while it's running
kubectl logs metricset-sample-l-0-0-d2kbq -f

# Save to log file
kubectl logs metricset-sample-l-0-0-d2kbq > size-128.log
kubectl delete -f metrics-128.yaml 
```

Save pods, in case we need:

```bash
kubectl get pods -o json > pods.json
```

I put the times together into [times.log](times.log) for plotting.
And delete the cluster:

```bash
gcloud container clusters delete osu-cluster
```


