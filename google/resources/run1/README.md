# Google Cloud Resources

This will reproduce [run0](../run0) but look at cgroups specifically and use hwloc
to see what each pod sees.

## c2d-standard-112

### Create the Cluster

Let's test a cluster on c2d-standard-112 for size 4.

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --num-nodes=4 \
    --region=us-central1-a \
    --project=${GOOGLE_PROJECT} \
    --machine-type=c2d-standard-112 \
    --placement-type=COMPACT \
    --system-config-from-file=./cluster-config.yaml
```

### Install the Flux Operator

We are going to install the Flux operator from the refactor branch (with the feature added to disable affinity).

```bash
git clone -b test-refactor-modular 
cd test-refactor-modular

# You might need other dependencies, etc. here or to specify your own registry you can push to.
make test-deploy-recreate
```

Save nodes.

```bash
kubectl get nodes -o json > nodes.json
```

### Looking at Resources with hwloc

I'm OK doing this manually since we are just doing it once! I'm going to first create a minicluster where there is 1 pod : 1 node, and then look at the output with lstopo along with what cgroups sees. Then I'll do the same, but break each pod into a few flux containers, and do the same.

#### 4 pods, 1:1 mapping

This should use the entire node for each pod.

```bash
kubectl apply -f minicluster-4.yaml
```

Get the top pod output:

```bash
kubectl top pod --containers=true > top-pod-1-1.txt
```

Shell in to each pod and install hwloc. We will run two commands to generate xml and png.

```bash
kubectl exec -it flux-sample-0-xxx bash
```
```console
yum install -y epel-release
dnf install -y hwloc hwinfo
mkdir -p /opt/info
hwloc-ls /opt/info/machine.xml
lscpu > /opt/info/lscpu.txt
cat /proc/cpuinfo > /opt/info/cpuinfo.txt
nproc --all > /opt/info/nproc.txt
hwinfo --all > /opt/info/hwinfo.txt
```

Do for each pod 0-3, and then save to the local machine.

```bash
mkdir -p data/1-1/0 data/1-1/1 data/1-1/2 data/1-1/3
kubectl cp flux-sample-0-mvwv6:/opt/info ./data/1-1/0/
```

I think for the broken apart case, we don't need to do this for every pod, just the containers on one. Delete when you are done:

```
kubectl delete -f minicluster-4.yaml
```

#### 6 "nodes" on 4 physical nodes

Do the same above, but with minicluster-6.yaml

```bash
kubectl apply -f minicluster-6.yaml
```

Which nodes are we on?

```
kubectl get pods -o wide
```
```
$ kubectl get pods -o wide
NAME                  READY   STATUS    RESTARTS   AGE   IP          NODE                                          NOMINATED NODE   READINESS GATES
flux-sample-0-4pmkm   1/1     Running   0          47s   10.8.1.25   gke-test-cluster-default-pool-50531823-12dr   <none>           <none>
flux-sample-1-slzw8   1/1     Running   0          46s   10.8.2.23   gke-test-cluster-default-pool-50531823-633f   <none>           <none>
flux-sample-2-cfrkn   1/1     Running   0          47s   10.8.0.24   gke-test-cluster-default-pool-50531823-0m78   <none>           <none>
flux-sample-3-mrzpr   1/1     Running   0          46s   10.8.1.26   gke-test-cluster-default-pool-50531823-12dr   <none>           <none>
flux-sample-4-mxljg   1/1     Running   0          46s   10.8.3.29   gke-test-cluster-default-pool-50531823-lnmh   <none>           <none>
```

Save data and pod metadata

```
mkdir -p data/multi
kubectl get pods -o json > data/multi/pods.json
for pod in flux-sample-0-4pmkm flux-sample-1-slzw8 flux-sample-2-cfrkn flux-sample-3-mrzpr  flux-sample-4-mxljg
  do
   mkdir -p data/multi/$pod
   kubectl cp ${pod}:/opt/info ./data/multi/$pod
done
```

And then I think I can manually look at that and (maybe?) see something interesting?
Note that flux-sample-0 and flux-sample-3 are sharing cpus.

## Thoughts

### Overview

This is really interesting. I couldn't even install software without OOMkilled and had to build a custom container that had it ready to go.
This tells us:

- Asking to scope resources via cgroups is going to make it unlikely basic workflows will run UNLESS they are good at controlling cpu/memory and won't go over.
- It's very likely when we run anything in Kubernetes, the pods are sharing resources constantly, and not setting the limits is the only way they wouldn't be killed.
- Our strategy of 1 pod: 1 node might be the only way to actually control this! And let flux handle instances to sub-partition resources.
- I also think this is (maybe?) was happening with Antonio - if we used his config to create resources, and we had the limits set (which I saw) it's likely lammps went over memory and MPI was killed first. I don't remember if I tried creating the cluster with the config after for the official experiments, but (will look) and if I did, maybe the difference was the amount of memory TODO CHECK THIS.

### Details

#### 1 pod : 1 node

Let's first sanity check that when we had 1 pod : 1 node, all of the resources (machines) looked the same. Note that I pulled down the hwloc xml files and generated pngs from them on my local machine.

![data/1-1/0/machine.png](data/1-1/0/machine.png)
![data/1-1/1/machine.png](data/1-1/1/machine.png)
![data/1-2/1/machine.png](data/1-1/2/machine.png)
![data/1-1/3/machine.png](data/1-1/3/machine.png)

I think the pictures might be cropped (note the 7x between the two sections)? But what I think I see is that:

- Each has two "Package" objects, each one associated with something called a NUMA node
- A NUMA node appears to be a grouping of resources (memory and CPU?)
- The caches go down from L3, L2, to L1, and L1 is where the CPU sit.
- If each NUMA node has 7x an L3 cache, and each L3 cache has 4 CPU, that means there are 7x4 == 28 CPU per package
  - This makes sense because the node has 56 total CPU (112 vCPU), so 2 packages (NUMA node) each with 28!

I think we can probably get details about location in the XML dumps (more than we can see in the picture). Since
they are all mostly the same, here [is one machine.xml](data/1-1/0/machine.xml).

#### 2 pod : 1 node

Now let's look at the case where there were TWO pods for one node. Note that I had an immensely hard time just getting one extra pod, because with the extra commands
it would often OOMKilled and I had to adjust the limits/requests (and decrease the total number down to 5 minicluster "nodes" on 4 actual nodes) to get this setup.
Likely we could get this into small increments with a simpler abstraction that doesn't require the Flux Operator to be installed. OK so firat, we know that flux-sample-0 and flux-sample-3 were sharing a node. Let's first add picture for that whole node (no parcellation):

![data/1-1/0/machine.png](data/1-1/0/machine.png)

And now let's add the output png for those two pods. What did they see?

| Flux Sample 0 | Flux Sample 3 |
|---------------|---------------|
| ![data/multi/flux-sample-0-4pmkm/machine.png](data/multi/flux-sample-0-4pmkm/machine.png) | ![data/multi/flux-sample-3-mrzpr/machine.png](data/multi/flux-sample-3-mrzpr/machine.png) |

Oh wow, OK! So...

- Flux sample 0 has ZERO access to any CPU in Package 1. Instead it seems to see Package 0:
 - 3/4 CPU for the first L3 cache 
 - 4/4 CPU for four x L3 
 - 1/4 CPU for the last L3
- So if there are 7x L3 caches for each NUMA node (package) this means we are only exposed to 5/7. And each isn't in entirety! For the above we have 3+(4*4)+1 CPU == 20 CPU

A lot of the above is likely because of the weird number I set (A fudged number t I could get working for CPU) which is 20. Now let's look at Flux sample 1:

- Flux sample 1 has access to both Package 0 and Package 1.
 - Package 0 has full access to 1 x L3 cache (4 CPU) + 3/4 CPU for a second (thus a total of 7 CPU)
 - Package 1 has full access to 3 x L3 caches (3x4 == 12 CPU) and ONE CPU in another L3 (total 13)

And thus 13 + 7 also == 20!

So I think we'd next want to understand how the CPU are located, as represented in the machine.xml or other metadata that I saved (see [data/multi](data/multi))
It looks like (at quick glance) the other commands I ran don't honor the cgroups, because I see all the CPU:

```
# This should not be 56
CPU(s):                          56
On-line CPU(s) list:             0-55

# E.g., this also should not be 56
L1d cache:                       1.8 MiB (56 instances)
L1i cache:                       1.8 MiB (56 instances)
L2 cache:                        28 MiB (56 instances)
L3 cache:                        448 MiB (14 instances)
```

I wonder if there are variants of those commands that are scoped to the cgroup? We can discuss / decide what to look at next.

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a --quiet
```
