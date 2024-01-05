# Fluence vs. Default Scheduler

At this point we have merged the automated testing and release of fluence, and want to try it here again (and reproduce the error and formally debug it). Likely before running experiments we want to fix any issues we see between the design (e.g., PodGroup) but getting the current version working first is most important. We will still be using:

 - [c2d-standard-8](https://cloud.google.com/compute/docs/compute-optimized-machines#c2d_machine_types)
  
## Experiments

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

We are going to follow the instructions from [the main repository](https://github.com/flux-framework/flux-k8s) to use the provided Fluence.

```bash
git clone --depth 1 https://github.com/flux-framework/flux-k8s.git
cd ./flux-k8s

# Prepare the manifests
make prepare
cd upstream/manifests/install/charts

# Check default values
helm show values as-a-second-scheduler

helm install schedscheduler-plugins as-a-second-scheduler/
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

<details>

<summary>Output for sidecar</summary>

```
Defaulted container "sidecar" out of: sidecar, scheduler-plugins-scheduler
This is the fluxion grpc server
Created flux resource client  &{0x23bf3d0}
&{ctx:0x23bf3d0}
Number nodes  5
node in flux group  gke-test-cluster-default-pool-1eab4ce5-7smv
Node  gke-test-cluster-default-pool-1eab4ce5-7smv  flux cpu  3
Node  gke-test-cluster-default-pool-1eab4ce5-7smv  total mem  29020379008
node in flux group  gke-test-cluster-default-pool-1eab4ce5-8s0p
Node  gke-test-cluster-default-pool-1eab4ce5-8s0p  flux cpu  3
Node  gke-test-cluster-default-pool-1eab4ce5-8s0p  total mem  29207936768
node in flux group  gke-test-cluster-default-pool-1eab4ce5-j6kg
Node  gke-test-cluster-default-pool-1eab4ce5-j6kg  flux cpu  3
Node  gke-test-cluster-default-pool-1eab4ce5-j6kg  total mem  29202693888
node in flux group  gke-test-cluster-default-pool-1eab4ce5-w921
Node  gke-test-cluster-default-pool-1eab4ce5-w921  flux cpu  3
Node  gke-test-cluster-default-pool-1eab4ce5-w921  total mem  29318037248
node in flux group  gke-test-cluster-default-pool-1eab4ce5-xzc0
Node  gke-test-cluster-default-pool-1eab4ce5-xzc0  flux cpu  3
Node  gke-test-cluster-default-pool-1eab4ce5-xzc0  total mem  29298037248
Can request at most  15  exclusive cpu
Match policy:  {"matcher_policy": "lonode"}
[GRPCServer] gRPC Listening on [::]:4242
[1]+  Done                    gedit README.md
```

</details>

Question - where does fluence get 3 cpu? The [nodes show 4 cpus](./results/nodes.json) available. I'm guessing this means 1cpu is being used. And you should see health checks here:

```bash
kubectl logs fluence-757fdcd854-cbqn2 -c scheduler-plugins-scheduler
```

### Flux Operator

Now let's install the Flux Operator from the development branch.

```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/test-refactor-modular/examples/dist/flux-operator-refactor.yaml
```

You can check logs to ensure it is also running, in the `operator-system` namespace.

### Experiment Prototyping

Ensure you have the same requirements installed.

```bash
pip install -r requirements.txt
```

#### Test Case

We have automation for experiments, but first let's manually test fluence.

```bash
kubectl apply -f ./crd/test-lammps.yaml
```

Ensure that the pods run, complete, and the logs look good! They did!! Yay!! Let's save the test run.
 
```bash
kubectl logs flux-sample-0-tcvqm > results/test-lammps.log
```

I saved a log for the [fluence sidecar](results/fluence-sidecar.log) so we can inspect the cancel response. Note that we probably want to remove the dump of the entire pod metadata (too verbose).

Now let's delete.

```bash
kubectl delete -f crd/test-lammps.yaml
```

#### Automated Case

The templates in [crd](crd) will be used to run experiments. Specifically we are expecting to find a `lammps.yaml`. Note that memory is in GiB, and we set the `--outdir` to create separation between experiment results.  Note that I removed the `--cpus` and `--memory` flag - it was manually added metadata just for a log that doesn't make sense (we could be wrong) and we can derive this programmatically if needed.

```bash
# Prototype with fluence
python run_experiments.py --outdir ./results/test-six --config-name lammps-six --fluence --iters 1
```
```console
▶️  Output directory: /home/vanessa/Desktop/Code/operator-experiments/google/scheduler/run4/results/test-six
▶️     Using Fluence: True
▶️       Config name: lammps-six
▶️        Iterations: 1
Would you like to continue? (yes/no)? yes
```

When it's running you can use `kubectl get pods` in another window to see the pods changing (add `--watch` for streaming updates). This all worked! This is fantastic! See [next steps](#next-steps) below for my suggested next steps. It will finish up and tell you that you are done! 

```
ited (rc=0) 1.4s
broker.info[0]: rc3-success: finalize->goodbye 1.42597s
broker.info[0]: goodbye: goodbye->exit 0.02148ms
Leader lammps-0-size-4-0-gkd8d is in phase Running
Leader lammps-0-size-4-0-gkd8d is in phase Running
minicluster.flux-framework.org "lammps-0-size-3" deleted

minicluster.flux-framework.org "lammps-0-size-2" deleted

minicluster.flux-framework.org "lammps-0-size-4" deleted

🧪️ Experiments are finished. See output in ./results/test-six
```

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```

## Suggested Next Steps

1. Discuss fluence issues / PodGroup issues, and test again.
2. Discuss output timings we need (right now I am not calculating and saving any timings)
3. Run experiments slightly larger scale as a test run
4. Discuss larger run / strategy!
