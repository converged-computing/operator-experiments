# Resource Test

This is a small experiment to see if the resource requests are honored, on Google cloud.
E.g., If we create a MiniCluster with >1 pod per node, does `flux resource list`
show the entire node, or limit? 

## Usage

Create the cluster:

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=2 \
    --machine-type=c2d-standard-8 \
    --enable-gvnic
```

Install (a development version) of the flux operator

```bash
kubectl apply -f ./examples/dist/flux-operator-dev.yaml
```

Then create a minicluster.

```bash
kubectl create namespace flux-operator
kubectl apply -f minicluster-1.yaml
```

Note that affinity rules aren't applied - you can assign > 1 pod per node.
That didn't seem to limit anything - we can see the pod resource limits/requests

```
    resources:
      limits:
        cpu: "2"
        memory: 14G
      requests:
        cpu: "2"
        memory: 14G
```

And we have 2 nodes, 4 cpu each, but we still "see" all of it.

```bash
     STATE NNODES   NCORES NODELIST
      free      2        8 flux-sample1-[0-1]
 allocated      0        0 
      down      0        0 
```

Cleanup.

```bash
gcloud container clusters delete test-cluster 
```

### Try with larger cluster

In case this one is just too small, let's go larger.

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=2 \
    --machine-type=c3-standard-176 \
    --enable-gvnic
```

Install (a development version) of the flux operator

```bash
kubectl apply -f ./examples/dist/flux-operator-dev.yaml
```

Then create a minicluster.

```bash
kubectl create namespace flux-operator
kubectl apply -f minicluster-1.yaml
```

Note that affinity rules aren't applied - you can assign > 1 pod per node.
That didn't seem to limit anything - we can see the pod resource limits/requests

```
    resources:
      limits:
        cpu: "2"
        memory: 14G
      requests:
        cpu: "2"
        memory: 14G
```

And then check that we are on separate nodes:

```
$ kubectl get pods -o wide -n flux-operator 
NAME                   READY   STATUS    RESTARTS   AGE   IP          NODE                                          NOMINATED NODE   READINESS GATES
flux-sample1-0-t87hb   1/1     Running   0          2m    10.8.1.9    gke-test-cluster-default-pool-8669f0f0-1ggm   <none>           <none>
flux-sample1-1-fr454   1/1     Running   0          2m    10.8.0.14   gke-test-cluster-default-pool-8669f0f0-5qv4   <none>           <none>
```

Shell in and see what we see for resources:

```bash
kubectl exec -it -n flux-operator flux-sample1-0-t87hb bash
```
```console
# flux resource list
     STATE NNODES   NCORES NODELIST
      free      2      176 flux-sample1-[0-1]
 allocated      0        0 
      down      0        0 
```
No that's off - we should see 2 nodes, and limited to 40 cpu (ncores) each for a total (between the two) of 80-88. Now let's try adding the memory limit
(the current [minicluster-2.yaml](minicluster-2.yaml).

```console
# flux resource list
     STATE NNODES   NCORES NODELIST
      free      2      176 flux-sample1-[0-1]
 allocated      0        0 
      down      0        0 
```

Still no go. As a last try, I'm going to add back the affinity rule. I got the same
result. So I cannot reproduce the cgroups setting to actually limit memory on the node. And
just to see:

```
# this is ~726 GB, no limit seems to be set
grep MemTotal /proc/meminfo
MemTotal:       726537812 kB
```

And just for debugging, here is the pod created (with the affinity rule, note the previous
cases don't have it, but we get the same result). [pods-with-affinity.yaml](pods-with-affinity.yaml).

Delete it all!

```bash
gcloud container clusters delete test-cluster 
```

