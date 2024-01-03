# Fluence vs. Default Scheduler

This is a testing setup for running an experiment to test fluence against the default scheduler.
We will use the instance type that we got working for LAMMPS previously.

 - [c2d-standard-8](https://cloud.google.com/compute/docs/compute-optimized-machines#c2d_machine_types)
  
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

We are going to follow the instructions from [the branch here](https://github.com/flux-framework/flux-k8s/pull/47) to build Fluence (I'll push to my own registry for now) and then install Fluence.

```bash
git clone -b modular-fluence-build https://github.com/flux-framework/flux-k8s.git
cd ./flux-k8s

# Build the custom images
make prepare
make build REGISTRY=vanessa
make build-sidecar REGISTRY=vanessa

docker push vanessa/fluence
docker push vanessa/fluence-sidecar

cd upstream/manifests/install/charts
helm install \
  --set scheduler.image=vanessa/fluence:latest \
  --set scheduler.sidecarimage=vanessa/fluence-sidecar:latest \
    schedscheduler-plugins as-a-second-scheduler/
```

Ensure both pods are running:

```bash
kubectl get pods
```
```console
NAME                                          READY   STATUS    RESTARTS   AGE
fluence-757fdcd854-cbqn2                      2/2     Running   0          24s
scheduler-plugins-controller-9f778469-c5wg9   1/1     Running   0          24s
```

You can check the logs for fluence to see the sidecar (that has fluence) and the main scheduler plugins pod (that should primarily have health checks).

```bash
kubectl logs fluence-757fdcd854-cbqn2 
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

Now let's apply the examples for basic testing.

```bash
kubectl apply -f example/
```

Ensure both pods are running, and that they were scheduled on fluence (vs the default scheduler)

```bash
kubectl get pods
```
```console
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

### Test Flux Operator

Now let's test the Flux Operator - if we add the indexed job pods to a PodGroup I think that should schedule them together?
First install the operator from the development branch.

```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/test-refactor-modular/examples/dist/flux-operator-refactor.yaml
```

And the example, which has a minicluster and a pod group:

```bash
kubectl apply -f crd/test-lammps.yaml 
```

And sanity check that the flux-sample was scheduled by fluence:

```bash
kubectl get events -o wide |  awk {'print $4" " $5" " $6'} | column -t | grep fluence
```

That's great! We can see that Fluence is able to schedule flux operator pods. We will next try this more in a context of launching multiple jobs (of different sizes) next.

### Canopie Experiments

**TODO** I don't know how to run qmcpack / amg, so right now I'd just do lammps at different pod sizes and problem sizes to emulate an ensemble of different workloads.
I started to reproduce with the MPI operator (below) but don't think this is the path we should take (see [canopie.md](canopie.md))

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```
