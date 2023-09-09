# Developing OSU/Chatterbug

Here we will test and develop the chatterbug and OSU benchmarks. This is just a testing cluster for now.
We don't have quota for c3 so we can use c2d.

## OSU Benchmarks

```bash
GOOGLE_PROJECT=myproject
gcloud compute networks create mtu9k --mtu=8896 
gcloud container clusters create osu-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=4 \
    --machine-type=c2d-standard-8 \
    --enable-gvnic
```

Install JobSet

```bash
VERSION=v0.2.0
kubectl apply --server-side -f https://github.com/kubernetes-sigs/jobset/releases/download/$VERSION/manifests.yaml
```

And the operator (I did from a development branch)! 
We first want to test if OSU can handle > 2 nodes (and for which benchmarks). I've built
a custom version.

```bash
kubectl apply -f metrics-osu-bechmarks.yaml 
```

This generated a log for ALL benchmarks and with timings, and that way we can decide on a subset:

 - [metrics-osu-benchmarks.log](metrics-osu-benchmarks.log)
 - [metrics-osu-benchmarks-times.log](metrics-osu-benchmarks-times.log)


And delete:

```bash
gcloud container clusters delete osu-cluster
```

I still need to do the same for chatterbug.

## Chatterbug

Bring up the cluster. We already have the network.

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create chatterbug-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=4 \
    --machine-type=c2d-standard-8 \
    --enable-gvnic
```

Install JobSet

```bash
VERSION=v0.2.0
kubectl apply --server-side -f https://github.com/kubernetes-sigs/jobset/releases/download/$VERSION/manifests.yaml
```

And the operator. Note that chatterbug can't even get far enough to print an error message. It feels janky, and doesn't have any updates since 2018. I'm erring on tending to not want to use it.

```
root@metricset-sample-l-0-0:~/chatterbug# mpirun --hostfile ./hostlist.txt --allorun-as-root -N 16 /root/chatterbug/ping-ping/ping-ping.x 
Warning: Permanently added '10.28.1.8' (ECDSA) to the list of known hosts.
Warning: Permanently added '10.28.1.7' (ECDSA) to the list of known hosts.
Warning: Permanently added '10.28.1.9' (ECDSA) to the list of known hosts.
^Croot@metricset-sample-l-0-0:~/chatterbug# mpirun --hostfile ./hostlist.txt --allorun-as-root -N 16 /root/chatterbug/stencil3d/stencil3d.x                   
Warning: Permanently added '10.28.1.8' (ECDSA) to the list of known hosts.
Warning: Permanently added '10.28.1.9' (ECDSA) to the list of known hosts.
Warning: Permanently added '10.28.1.7' (ECDSA) to the list of known hosts.
^Croot@metricset-sample-l-0-0:~/chatterbug# mpirun --hostfile ./hostlist.txt --allow-run-as-root /root/chatterbug/stencil3d/stencil3d.x
Warning: Permanently added '10.28.1.8' (ECDSA) to the list of known hosts.
Warning: Permanently added '10.28.1.9' (ECDSA) to the list of known hosts.
Warning: Permanently added '10.28.1.7' (ECDSA) to the list of known hosts.
```

I don't have confidence in these metrics enough to present or have them represent our community, and I'm not going to pursue them further.
Then delete the cluster.

```
gcloud container clusters delete chatterbug-cluster
```
