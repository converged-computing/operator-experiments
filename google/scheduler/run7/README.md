# Fluence vs. Default Scheduler

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

# Size 2 and 3 (clogged)
mkdir -p ./results/size-2-3
time python run_experiments.py --outdir ./results/size-2-3/test-fluence --config-name lammps-two-three --fluence --batches 1 --iters 20
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

### Plotting

Note that this script currently has the specific experiment folder hard coded. E.g., batch-3 was a smaller run with 5 iterations per run, and one larger run.

```bash
python plot-lammps.py
```
```console
scheduler         experiment   
default           size-16-8-8-8    231.673912
                  size-4-8-8-8     278.769004
                  size-8-8-8-8     200.557229
fluence           size-16-8-8-8    332.043333
                  size-4-8-8-8     417.339467
                  size-8-8-8-8     363.893496
fluence-original  size-16-8-8-8    333.007603
                  size-4-8-8-8     419.829057
                  size-8-8-8-8     359.630531
Name: total_time, dtype: object
scheduler         experiment   
default           size-16-8-8-8    170.809912
                  size-4-8-8-8     168.904840
                  size-8-8-8-8     135.923852
fluence           size-16-8-8-8    157.394845
                  size-4-8-8-8     158.262492
                  size-8-8-8-8     160.588298
fluence-original  size-16-8-8-8    159.947619
                  size-4-8-8-8     159.312676
                  size-8-8-8-8     155.889868
Name: total_time, dtype: float64
```

## Some Notes

I did these runs many times, often because I was debugging. I learned the following:

 - What I am calling "clogging" of having jobs scheduled that can't run I think is less a reflection of the scheduler (it happened for all of them) and more a reflection on the inability of the Flux Operator to allow for starting without all the ranks. I set a very strict criteria at first of requiring all pods for the group _and_ the Flux Operator needing all to start, so if there was ever a case of variation of a few pods (for whatever reason) the queue could block. Making the Flux Operator more robust to starting seemed to patch this, at least for now, allowing the experiment to run in full.
 - The timings I'm taking are rough at best - the total wall time is easy, but the start / end time are from the point of job submission to the end of LAMMPS running. This (we assume) includes the LAMMPS wall time plus time to schedule and then brokers to hook up. We likely can get better breakdown of logging and timing if I know where to look.
 - [batch-3](batch-3): includes the results of interest. For batch-2, I took the end time after events parsing, so it doesn't reflect when the lammps run actually finished (but added time to it). I also removed any "raise" from running the experiment, because it would happen in a multiprocess worker and sort of freeze things up.
 - The way we are running experiments here (with multiprocessing) I don't love. Sometimes it hangs at the end and I don't know why.

I'll write up a post for what I learned. For the actual experiment here, I found using multiprocessing a bit buggy at times - workers would freeze when everything appeared done between a batch. Likely we need a better way to submit many at the same time, maybe via a functions as a service sort of deal? Or even Flux jobs? This might actually be suited for a workflow tool, but which one will need further thought. I've noticed it's really hard automating running stuff with Kubernetes - maybe the hardest part of these experiments. I hope we can do better. The other thing I did wrong here was to put the number of tasks as larger than the minimum size that could be run. This meant that in those edge cases when a worker or workers couldn't join the cluster, it could not start with fewer because there were not enough tasks exposed.

### Suggested Next Steps

- Discuss the design of the experiment in the context of the Flux Operator
 - I want to understand how/where we should be getting times from.
- Walk through the entire logic of scheduling a single Minicluster, and confirm that:
 - The resources we are asking for are what fluxion is getting
 - The assignment of nodes we get back is correctly handed to pods
 - What happens in edge cases and events (batch pod scheduling, pod added back to queue, etc).
 - Write down every step in the fluence code and verify working as expected.

We likely will need to consider how the Flux Operator works in this context, because it's
different than the MPI operator.
