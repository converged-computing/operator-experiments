# Fluence vs. Default Scheduler

This is a testing setup for running an experiment to test fluence against the default scheduler.
We will use the instance type that we got working for LAMMPS previously.

 - [c2d-standard-8](https://cloud.google.com/compute/docs/compute-optimized-machines#c2d_machine_types)

Note that the difference between [run0](../run0) is that we are using a WIP branch with the Fluence
scheduler fixed.
  
## Experiments

### Create the Cluster

Let's test a cluster on c2d-standard-8 for size 4. Note that I'm leaving out the network optimization.
We will follow [these best practices](https://cloud.google.com/architecture/best-practices-for-using-mpi-on-compute-engine).

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=4 \
    --region=us-central1-a \
    --project=${GOOGLE_PROJECT} \
    --machine-type=c2d-standard-8
```

### Install the Scheduler

We are going to follow the instructions from [the changes here](https://github.com/flux-framework/flux-k8s/pull/42) to install Fluence.

```bash
git clone https://github.com/researchapps/scheduler-plugins.git -b pull-upstream-into-fluence
cd scheduler-plugins/manifests/install/charts

# Note that I had already just built these
helm install \
  --set scheduler.image=vanessa/fluence:latest \
  --set scheduler.sidecarimage=vanessa/fluence-sidecar \
    schedscheduler-plugins as-a-second-scheduler/
```

Ensure both pods are running:

```bash
$ kubectl get pods
```
```console
NAME                                          READY   STATUS    RESTARTS   AGE
fluence-757fdcd854-cbqn2                      2/2     Running   0          24s
scheduler-plugins-controller-9f778469-c5wg9   1/1     Running   0          24s
```

You can check the logs for fluence to see the sidecar (that has fluence) and the main scheduler plugins pod (that should primarily have health checks).

```bash
$ kubectl logs fluence-757fdcd854-cbqn2 
```
```
Defaulted container "sidecar" out of: sidecar, scheduler-plugins-scheduler
This is the fluxion grpc server
Created cli context  &{}
&{}
Number nodes  4
node in flux group  gke-test-cluster-default-pool-92dbd7e9-bgv5
Node  gke-test-cluster-default-pool-92dbd7e9-bgv5  flux cpu  3
Node  gke-test-cluster-default-pool-92dbd7e9-bgv5  total mem  29207936768
node in flux group  gke-test-cluster-default-pool-92dbd7e9-h4sc
Node  gke-test-cluster-default-pool-92dbd7e9-h4sc  flux cpu  3
Node  gke-test-cluster-default-pool-92dbd7e9-h4sc  total mem  29202693888
node in flux group  gke-test-cluster-default-pool-92dbd7e9-ln89
Node  gke-test-cluster-default-pool-92dbd7e9-ln89  flux cpu  3
Node  gke-test-cluster-default-pool-92dbd7e9-ln89  total mem  29298037248
node in flux group  gke-test-cluster-default-pool-92dbd7e9-xzb4
Node  gke-test-cluster-default-pool-92dbd7e9-xzb4  flux cpu  3
Node  gke-test-cluster-default-pool-92dbd7e9-xzb4  total mem  29020379008
Can request at most  12  exclusive cpu
Match policy:  {"matcher_policy": "lonode"}
[GRPCServer] gRPC Listening on [::]:4242
```

And you should see health checks here:

```bash
kubectl logs fluence-757fdcd854-cbqn2 -c scheduler-plugins-scheduler
```

### Example Scheduling

Now let's apply the examples:

```bash
kubectl apply -f example/
```

Ensure both pods are running, and that they were scheduled on fluence (vs the default scheduler)

```bash
NAME                                          READY   STATUS    RESTARTS   AGE
default-scheduler-pod                         1/1     Running   0          20s
fluence-757fdcd854-cbqn2                      2/2     Running   0          3m4s
fluence-scheduled-pod                         1/1     Running   0          20s
scheduler-plugins-controller-9f778469-c5wg9   1/1     Running   0          3m4s
```
```bash
kubectl get events -o wide |  awk {'print $4" " $5" " $6'} | column -t
```
```console
REASON                                            OBJECT                                         SUBOBJECT
pod/default-scheduler-pod                         default-scheduler                              Successfully
pod/default-scheduler-pod                         spec.containers{default-scheduler-container}   kubelet,
pod/default-scheduler-pod                         spec.containers{default-scheduler-container}   kubelet,
pod/default-scheduler-pod                         spec.containers{default-scheduler-container}   kubelet,
pod/default-scheduler-pod                         spec.containers{default-scheduler-container}   kubelet,
pod/fluence-757fdcd854-cbqn2                      default-scheduler                              Successfully
pod/fluence-757fdcd854-cbqn2                      spec.containers{sidecar}                       kubelet,
pod/fluence-757fdcd854-cbqn2                      spec.containers{sidecar}                       kubelet,
pod/fluence-757fdcd854-cbqn2                      spec.containers{sidecar}                       kubelet,
pod/fluence-757fdcd854-cbqn2                      spec.containers{sidecar}                       kubelet,
pod/fluence-757fdcd854-cbqn2                      spec.containers{scheduler-plugins-scheduler}   kubelet,
pod/fluence-757fdcd854-cbqn2                      spec.containers{scheduler-plugins-scheduler}   kubelet,
pod/fluence-757fdcd854-cbqn2                      spec.containers{scheduler-plugins-scheduler}   kubelet,
pod/fluence-757fdcd854-cbqn2                      spec.containers{scheduler-plugins-scheduler}   kubelet,
replicaset/fluence-757fdcd854                     replicaset-controller                          Created
pod/fluence-scheduled-pod                         fluence,                                       fluence-fluence-757fdcd854-cbqn2
```

And that's it - I think we are unblocked now for testing the fluence scheduler on GCP.  Delete those pods.

```bash
kubectl delete -f example/
```

### Canopie Experiments

#### MPI Operator

We aren't going to use the Python template script, but rather just install the operator.
Install the MPI operator first:

```bash
kubectl apply -f ./experiments/mpi-operator.yaml
```

#### Taints

The next step has us tainting nodes with the label fluence ([done here](https://github.com/flux-framework/flux-k8s/blob/e4b2dc20c095ba95a7217065349e30ee9bb34723/canopie22-artifacts/kube_setup/eks-efa-cluster-config.yaml#L34)). We will do that for now to reproduce the MPI operator, but when we change to the Flux operator we won't need to do that. We also aren't creating nodes with eksctl so we don't have labels, so we are going to manually hack it for now. From [here](https://github.com/flux-framework/flux-k8s/blob/canopie22-artifacts/canopie22-artifacts/kube_setup/eks-efa-cluster-config.yaml) we can see there are 32 workers and 2 launchers, so let's do 1 launcher and 3 workers. E.g., 4 nodes:

```bash
NAME                                          STATUS   ROLES    AGE   VERSION
gke-test-cluster-default-pool-92dbd7e9-bgv5   Ready    <none>   21m   v1.27.3-gke.100
gke-test-cluster-default-pool-92dbd7e9-h4sc   Ready    <none>   21m   v1.27.3-gke.100
gke-test-cluster-default-pool-92dbd7e9-ln89   Ready    <none>   21m   v1.27.3-gke.100
gke-test-cluster-default-pool-92dbd7e9-xzb4   Ready    <none>   21m   v1.27.3-gke.100
```

Note that I decided to not do this, because I don't care if the scheduling is a bit wonky for this test.
But you theoretically could choose one for the launcher and give the same taints / labels:

```bash
launcher=gke-test-cluster-default-pool-92dbd7e9-bgv5
kubectl taint nodes $launcher launcher=true:NoSchedule-
```

Do the same for the workers, but as a worker:

```bash
kubectl taint nodes gke-test-cluster-default-pool-92dbd7e9-h4sc worker=true:NoSchedule-
kubectl taint nodes gke-test-cluster-default-pool-92dbd7e9-ln89 worker=true:NoSchedule-
kubectl taint nodes gke-test-cluster-default-pool-92dbd7e9-xzb4 worker=true:NoSchedule-
```

The original script to taint is [here](https://github.com/flux-framework/flux-k8s/blob/canopie22-artifacts/canopie22-artifacts/kube_setup/taint_workers.sh) and the labels from eksctl are [here](https://github.com/flux-framework/flux-k8s/blob/canopie22-artifacts/canopie22-artifacts/kube_setup/eks-efa-cluster-config.yaml)

#### Dummy Experiment Run

We next want to proceed to try the [experiments here](https://github.com/flux-framework/flux-k8s/tree/canopie22-artifacts/canopie22-artifacts). We are [starting here](https://github.com/flux-framework/flux-k8s/tree/canopie22-artifacts/canopie22-artifacts#running-experiments-with-amg-lammps-and-qmcpack). For provenance, I have cloned and copied the Dockerfile and yaml here and refactored them from templates into just yaml.

 - [experiments](experiments)
  - [lammps](experiments/lammps)

We can largely use the same containers referenced in the yamls. For example:

```bash
cd experiments/lammps

# run a small 2x2x2 problem on 12 processes
kubectl apply -f lammps_mpijob.yaml
```

Note some changes detailed [here]() about PodGroup (that are reflected in the lammps yaml above).
Note that I got some errors in the launcher:

```bash
kubectl logs lammps-launcher-xxxx
```
```console
++ unset i
+ mpirun --allow-run-as-root --mca orte_launch_agent /opt/view/bin/orted --mca plm_rsh_agent rsh -x PATH -x LD_LIBRARY_PATH -np 12 --map-by socket lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
bash: line 1:     8 Illegal instruction     (core dumped) mpirun --allow-run-as-root --mca orte_launch_agent /opt/view/bin/orted --mca plm_rsh_agent rsh -x PATH -x LD_LIBRARY_PATH -np 12 --map-by socket lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
real 0.01
user 0.00
sys 0.01
```

And the workers logically did not do anything interesting:

```bash
kubectl logs lammps-worker-0
```
```console
Server listening on 0.0.0.0 port 22.
Server listening on :: port 22.
kex_exchange_identification: Connection closed by remote host
```

I tried an interactive test to see if I could run something, and it seems that there is some issue with this container on the node possibly? A basic lammps run did not work.

```bash
docker run -it milroy1/kf-testing:lammps-focal-openmpi-4.1.2 bash
```
```console
# ./lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
Illegal instruction (core dumped)
```

So that is a good stopping point. My suggestions for next steps are to:

- Decide if we want to use the MPI operator (or switch to the Flux Operator)
- Rebuild base containers with updated versions of things
- Re-do an experiment with these updates.

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a --quiet
```
