# Fluence vs. Default Scheduler

This is a testing setup for running an experiment to test fluence against the default scheduler.
We will use the instance type that we got working for LAMMPS previously.

 - [c2d-standard-8](https://cloud.google.com/compute/docs/compute-optimized-machines#c2d_machine_types)
  
## Experiments

### Create the Cluster

Note that for testing, you can create a cluster with kind. This will create a control plane and 4 nodes.

```bash
kind create cluster --config ./crd/kind-config.yaml
```

<details>
<summary>kubectl get nodes</summary>

```console
NAME                 STATUS   ROLES           AGE   VERSION
kind-control-plane   Ready    control-plane   78s   v1.27.3
kind-worker          Ready    <none>          54s   v1.27.3
kind-worker2         Ready    <none>          54s   v1.27.3
kind-worker3         Ready    <none>          55s   v1.27.3
```

</details>

I found when I needed to do actual multiple runs, I needed a real cluster.
After prototyping, you can create a cluster on c2d-standard-8 for size 4. Note that I'm leaving out the network optimization. We will follow [these best practices](https://cloud.google.com/architecture/best-practices-for-using-mpi-on-compute-engine).

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=5 \
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

### Flux Operator

Now let's install the Flux Operator from the development branch.

```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/test-refactor-modular/examples/dist/flux-operator-refactor.yaml
```

### Experiment Prototyping

 - *TODO*: check if a [Pod group](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/kep/42-podgroup-coscheduling/README.md) needs to be unique to specific pods (it seems so)?

We've already tested that examples work here in [run2](../run2) so let's go right into running experiments with Fluence. We will use a modified [run_experiments.py](run_experiments.py) that templates a [lammps.yaml](lammps.yaml) file.
First, create a virtual Python environment (your preferred way) and install dependencies:

```bash
pip install -r requirements.txt
```

The templates in [crd](crd) will be used to run experiments. Specifically we are expecting to find a `lammps.yaml`. Let's run experiments, here are a few examples. Note that memory is in GiB, and we set the `--outdir` to create separation between experiment results. Also note that fluence doesn't seem to be working yet - we need to merge in the current work and come back here to test again.

```bash
# Prototype with default scheduler
python run_experiments.py --cpus 24 --memory 192 --outdir ./results/test-six --config-name lammps-six
```
```console
▶️  Output directory: /home/vanessa/Desktop/Code/operator-experiments/google/scheduler/run3/results/test-six
▶️   Memory per node: 192
▶️     CPUs per node: 24
▶️     Using Fluence: False
▶️       Config name: lammps-six
▶️        Iterations: 10
Would you like to continue? (yes/no)? yes
```

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```

## Suggested Next Steps

1. Merge in current PRs (two essential) for Fluence
2. Debug issue here with nil value
3. Do testing with Fluence here
4. Discuss output timings we need (right now I am not calculating and saving any timings)
5. Run experiments slightly larger scale as a test run
6. Discuss larger run / strategy

