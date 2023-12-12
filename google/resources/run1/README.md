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

### Thoughts

This is really interesting. I couldn't even install software without OOMkilled and had to build a custom container that had it ready to go.
This tells us:

- Asking to scope resources via cgroups is going to make it unlikely basic workflows will run UNLESS they are good at controlling cpu/memory and won't go over.
- It's very likely when we run anything in Kubernetes, the pods are sharing resources constantly, and not setting the limits is the only way they wouldn't be killed.
- Our strategy of 1 pod: 1 node might be the only way to actually control this! And let flux handle instances to sub-partition resources.
- I also think this is (maybe?) was happening with Antonio - if we used his config to create resources, and we had the limits set (which I saw) it's likely lammps went over memory and MPI was killed first. I don't remember if I tried creating the cluster with the config after for the official experiments, but (will look) and if I did, maybe the difference was the amount of memory TODO CHECK THIS.

TODO: look at data and figure out resource sharing.

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a --quiet
```
