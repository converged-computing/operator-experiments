# Fluence vs. Default Scheduler

We are still trying to get this base case working. We are using this instance type.

 - [c2d-standard-8](https://cloud.google.com/compute/docs/compute-optimized-machines#c2d_machine_types)
  
## Experiments

After prototyping, you can create a cluster on c2d-standard-8 for a size of interest. Note that I'm leaving out the network optimization. We will follow [these best practices](https://cloud.google.com/architecture/best-practices-for-using-mpi-on-compute-engine).

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=8 \
    --region=us-central1-a \
    --project=${GOOGLE_PROJECT} \
    --machine-type=c2d-standard-8
```

### Install Cert Manager

The newer version of fluence requires the certificate manager. There is likely a way to do self-signed certs but we haven't tried it yet.

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.1/cert-manager.yaml
```

### Flux Operator

Now let's install the Flux Operator from the development branch test-refactor-modular. I did this locally.

```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/main/examples/dist/flux-operator.yaml
make test-deploy-recreate
```

You can check logs to ensure it is also running, in the `operator-system` namespace.

### Install the Scheduler

We are going to follow the instructions from [the main repository](https://github.com/flux-framework/flux-k8s) to use the provided Fluence, but use a [custom branch](https://github.com/flux-framework/flux-k8s/compare/testing-pod-group?expand=1) we are working on.

```bash
git clone --depth 1 --brance fluence-controller https://github.com/flux-framework/flux-k8s.git
cd ./flux-k8s

# These build each of the images. The sidecar is separate from the other two in src/
REGISTRY=ghcr.io/vsoch
make REGISTRY=${REGISTRY} SCHEDULER_IMAGE=fluence SIDECAR_IMAGE=fluence-sidecar CONTROLLER_IMAGE=fluence-controller

# This is what it might look like to push
docker push ghcr.io/vsoch/fluence-sidecar
docker push ghcr.io/vsoch/fluence-controller
docker push ghcr.io/vsoch/fluence:latest

# And then install using the charts. The pull policy ensures we use the loaded ones
cd ./upstream/manifests/install/charts
helm install \
  --set scheduler.image=${REGISTRY}/fluence:latest \
  --set controller.image=${REGISTRY}/fluence-controller:latest \
  --set scheduler.sidecarimage=${REGISTRY}/fluence-sidecar:latest \
        fluence as-a-second-scheduler/
```

Ensure both scheduler pods are running:

```bash
kubectl get pods
```
```console
NAME                                          READY   STATUS    RESTARTS   AGE
fluence-757fdcd854-cbqn2                      2/2     Running   0          24s
scheduler-plugins-controller-9f778469-c5wg9   1/1     Running   0          24s
```

Note that we saved the image manifests to save the exact digests that we used.
You can check the logs for fluence to see the sidecar (that has fluence) and the main scheduler plugins pod (that should primarily have health checks).

```bash
kubectl logs fluence-757fdcd854-cbqn2 
kubectl get pods -o json > results/scheduler-pods.json
kubectl get nodes -o json > results/nodes.json
```

### Experiment Prototyping

Ensure you have the same requirements installed.

```bash
pip install -r requirements.txt
```

#### Pull Container

Note that I made an indexed job to run on all nodes just to pull containers before running anything.

```bash
kubectl apply -f crd/pull-container.yaml
kubectl delete -f crd/pull-container.yaml
```

Note that I didn't make one for the init (flux view) container - we will want to do this in the future, otherwise the first experiment run will include pull of rocky. It's a trivial time but still important.

#### Automated Case

The templates in [crd](crd) will be used to run experiments. Specifically we are expecting to find a `lammps.yaml`. Note that memory is in GiB, and we set the `--outdir` to create separation between experiment results.  Note that I removed the `--cpus` and `--memory` flag - it was manually added metadata just for a log that doesn't make sense (we could be wrong) and we can derive this programmatically if needed. Also note that before running any experiments you should be sure that you have already pulled containers to each node (this typically happens through testing).

```bash
# Size 2: no clogging!
mkdir -p ./results/size-2
time python run_experiments.py --outdir ./results/size-2/test-fluence --config-name lammps-two --fluence --batches 1 --iters 20

# Size 2 and 3 (no clogging)
mkdir -p ./results/size-2-3
time python run_experiments.py --outdir ./results/size-2-3/test-fluence --config-name lammps-two-three --fluence --batches 1 --iters 20

# Lammps 2,3,4 (no clogging)
mkdir -p ./results/lammps-two-three-four
time python run_experiments.py --outdir ./results/lammps-two-three-four/test-fluence --config-name lammps-two-three-four --fluence --batches 1 --iters 20

# Lammps 2,3,4 with shuffle (no clogging)
mkdir -p ./results/lammps-two-three-four-shuffle
time python run_experiments.py --outdir ./results/lammps-two-three-four-shuffle/test-fluence --config-name lammps-two-three-four --fluence --batches 1 --iters 20  --shuffle

# Do 2 (cpu 1) and 3 (cpu 2) requests
mkdir -p ./results/lammps-two-three-cpu
time python run_experiments.py --outdir ./results/lammps-two-three-cpu/test-fluence --config-name lammps-two-three-cpu --fluence --batches 1 --iters 20

# 2,3,4,5,6
mkdir -p ./results/lammps-six
time python run_experiments.py --outdir ./results/lammps-six/test-fluence --config-name lammps-six --fluence --batches 1 --iters 10

# 2,3,4,5,6 then 2 (1 cpu), 3/4/5/6 (2 cpu)
mkdir -p ./results/lammps-mixed
time python run_experiments.py --outdir ./results/lammps-mixed/test-fluence --config-name lammps-mixed --fluence --batches 1 --iters 10
```
 

Delete the fluence pods after that with helm uninstall, and then helm uninstall fluence.

```
# without fluence (same setup as above)
time python run_experiments.py --outdir ./results/batch-2/test-six --config-name lammps-six --batches 1 --iters 20
```
```console
▶️  Output directory: /home/vanessa/Desktop/Code/operator-experiments/google/scheduler/run5/results/test-large
▶️     Using Fluence: True
▶️       Config name: lammps-large
▶️        Iterations: 30
▶️           Batches: 1
Would you like to continue? (yes/no)? 
```

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```
