# Fluence vs. Default Scheduler

> with added min size

I ran into an issue of the Flux MiniCluster locking, the reason being that I couldn't ask for a smaller group than the size scheduled.
For this experiment I want to do the same as before, but use an added `minSize` parameter that is the minimum size allowed for Flux to run the job.
This means we will schedule (create pod groups) for a size, but allow to start smaller than that. I'm hoping this better handles edge cases of the jobs locking and not being able to start, because we will always ask for a little larger than what we need.

 - [c2d-standard-8](https://cloud.google.com/compute/docs/compute-optimized-machines#c2d_machine_types)
  
## Experiments

After prototyping, you can create a cluster on c2d-standard-8 for a size of interest. Note that I'm leaving out the network optimization. We will follow [these best practices](https://cloud.google.com/architecture/best-practices-for-using-mpi-on-compute-engine).

```bash
GOOGLE_PROJECT=myproject
gcloud compute networks create mtu9k --mtu=8896 
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=149 \
    --region=us-central1-a \
    --project=${GOOGLE_PROJECT} \
    --machine-type=c2d-standard-8 \
    --enable-gvnic \
    --network=mtu9k \
    --system-config-from-file=./crd/system-config.yaml
```

### Install the Scheduler

We are going to follow the instructions from [the main repository](https://github.com/flux-framework/flux-k8s) to use the provided Fluence, but use a [custom branch](https://github.com/flux-framework/flux-k8s/compare/testing-pod-group?expand=1) we are working on.

```bash
git clone --depth 1 https://github.com/flux-framework/flux-k8s.git
cd ./flux-k8s
git fetch
git checkout testing-pod-group

# Prepare the manifests
make prepare REGISTRY=ghcr.io/vsoch
docker push ghcr.io/vsoch/fluence:latest && docker push ghcr.io/vsoch/fluence-sidecar:latest 
cd upstream/manifests/install/charts

# Check default values
helm show values as-a-second-scheduler

helm install \
  --set scheduler.image=ghcr.io/vsoch/fluence:latest \
  --set scheduler.sidecarimage=ghcr.io/vsoch/fluence-sidecar:latest \
        schedscheduler-plugins as-a-second-scheduler/
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

### Flux Operator

Now let's install the Flux Operator from the development branch test-refactor-modular. I did this locally.

```bash
make test-deploy-recreate
```

You can check logs to ensure it is also running, in the `operator-system` namespace.

### Experiment Prototyping

Ensure you have the same requirements installed.

```bash
pip install -r requirements.txt
```

#### Test Cases

I tested sizes 64 down to 8 (see in [crd](crd))
Ensure that the pods run, complete, and the logs look good! They did!! Yay!! Let's save the test run.
 
```bash
kubectl logs flux-sample-0-tcvqm
```

Note that you can tweak that yaml until you get the time / settings that you want.

```bash
kubectl delete -f crd/test-lammps.yaml
```

#### Pull Container

Note that I made an indexed job to run on all nodes just to pull containers before running anything.

```bash
kubectl apply -f crd/pull-container.yaml
kubectl apply -f crd/pull-container.yaml
```

Note that I didn't make one for the init (flux view) container - we will want to do this in the future, otherwise the first experiment run will include pull of rocky. It's a trivial time but still important.

#### Automated Case

The templates in [crd](crd) will be used to run experiments. Specifically we are expecting to find a `lammps.yaml`. Note that memory is in GiB, and we set the `--outdir` to create separation between experiment results.  Note that I removed the `--cpus` and `--memory` flag - it was manually added metadata just for a log that doesn't make sense (we could be wrong) and we can derive this programmatically if needed. Also note that before running any experiments you should be sure that you have already pulled containers to each node (this typically happens through testing).

```bash
# Adjust this to your needs
mkdir -p ./results/batch-4
time python run_experiments.py --outdir ./results/batch-4/test-large-fluence --config-name lammps-large --fluence --batches 1 --iters 20
# 11 minutes
```

Delete the fluence pods after that with helm uninstall. Then I installed the current fluence main branch (that does not have any changes):

```bash
helm uninstall schedscheduler-plugins
helm install schedscheduler-plugins as-a-second-scheduler/

time python run_experiments.py --outdir ./results/batch-4/test-original-fluence --config-name lammps-large --fluence --batches 1 --iters 20
```

And then uninstalled fluence entirely.

```
# without fluence (same setup as above)
time python run_experiments.py --outdir ./results/batch-4/test-large --config-name lammps-large --batches 1 --iters 20
```
```console
▶️  Output directory: /home/vanessa/Desktop/Code/operator-experiments/google/scheduler/run5/results/test-large
▶️     Using Fluence: True
▶️       Config name: lammps-large
▶️        Iterations: 30
▶️           Batches: 1
Would you like to continue? (yes/no)? 
```

And then more batches, 4 jobs each iteration, so 4 * 5 * 5 total jobs.

```bash
python run_experiments.py --outdir ./results/test-large --config-name lammps-large --batches 5 --iters 5
python run_experiments.py --outdir ./results/test-large-fluence --config-name lammps-large --fluence --batches 5 --iters 5
```

When it's running you can use `kubectl get pods` in another window to see the pods changing (add `--watch` for streaming updates). This all worked! 

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
