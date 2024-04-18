# Fluence vs. Default Scheduler vs. Cosheduling

Now that we have something working, let's run experiments. We want to compare:

1. Fluence
2. The default scheduler
3. The default scheduler with Kueue
4. Coscheduling

We don't need to run particularly large jobs for this, just an ensemble of one application at different sizes.
We can use the [c2d-standard-8](https://cloud.google.com/compute/docs/compute-optimized-machines#c2d_machine_types) machine type. We likely want to collect:

1. Time from submit to job completion (complete turn around time)
2. Time for the actual job to run (should not vary!)
3. If/ when a scheduler setup clogs (and the queue stops moving, likely only default kueue scheduler)
 
For experiment prototyping see [run9](../run9).
 
## Experiments

After prototyping, you can create a cluster on c2d-standard-8 for a size of interest. Note that I'm leaving out the network optimization. We will follow [these best practices](https://cloud.google.com/architecture/best-practices-for-using-mpi-on-compute-engine).

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=8 \
    --no-enable-autorepair \
    --no-enable-autoupgrade \
    --region=us-central1-a \
    --project=${GOOGLE_PROJECT} \
    --machine-type=c2d-standard-8
```

### Default Scheduler

Let's start with the default scheduler. Note that these run pretty fast (so maybe clogging unlikely) and we probably can eventually increase the iterations.

```bash
mkdir -p ./results/mixed
time python run_experiments.py --outdir ./results/mixed/kube-sched --config-name mixed --batches 1 --iters 10
```

It will clog sooner or later.

```console
$ kubectl get pods | grep Running
job-0-0-size-4-0-jjd8c   1/1     Running   0          8m45s
job-0-0-size-4-1-984rr   1/1     Running   0          8m45s
job-0-0-size-4-2-654kp   1/1     Running   0          8m45s
job-0-1-size-2-1-z4kd4   1/1     Running   0          8m43s
job-0-1-size-4-0-6mvww   1/1     Running   0          8m42s
job-0-2-size-3-0-6x2t7   1/1     Running   0          8m40s
job-0-7-size-5-0-qf7d2   1/1     Running   0          8m25s
job-0-7-size-5-2-phgpl   1/1     Running   0          8m25s
```

Save the state of the pods

```bash
kubectl get pods -o json > ./results/default-clogged-pods.json
```

```bash
$ kubectl get pods | grep Pending | wc -l
187
$ kubectl get pods | grep Running | wc -l
8
```

Cancel the experiment and clean up.

```bash
kubectl delete jobs --all
kubectl delete service --all
```

### Coscheduling

Let's follow instructions [from here](https://scheduler-plugins.sigs.k8s.io/docs/user-guide/installation/#as-a-second-scheduler)

```bash
git clone --depth 1 https://github.com/kubernetes-sigs/scheduler-plugins /tmp/sp
cd /tmp/sp/manifests/install/charts
```

Important!! Open up the `as-a-second-scheduler/values.yaml` config and update the default timeout to 5 minutes (see below). It won't work at the default (one minute) or what this was set to (10 seconds).

```yaml
# Customize the enabled plugins' config.
# Refer to the "pluginConfig" section of manifests/<plugin>/scheduler-config.yaml.
# For example, for Coscheduling plugin, you want to customize the permit waiting timeout to 10 seconds:
pluginConfig:
- name: Coscheduling
  args:
    permitWaitingTimeSeconds: 300 # default is 60
# Or, customize the other plugins
# - name: NodeResourceTopologyMatch
#   args:
#     scoringStrategy:
#       type: MostAllocated # default is LeastAllocated
#- name: SySched
#  args:
#    defaultProfileNamespace: "default"
#    defaultProfileName: "full-seccomp"
```

Then do:

```bash
helm install coscheduling as-a-second-scheduler/
```

Note this installs coscheduling et al as `scheduler-plugins-scheduler`. You can see the config with:

```bash
kubectl describe cm scheduler-config 
```

Let's run an experiment:

```bash
time python run_experiments.py --outdir ./results/mixed/coscheduling --config-name mixed --batches 1 --iters 10 --coscheduling
```

And then uninstall

```bash
helm uninstall coscheduling
```

### Kueue 

I'm trying Kueue first this time, before installing the cert manager, because I suspect that was related to the bug.

```console
# This is how I got the original one
# VERSION=v0.6.2
# wget https://github.com/kubernetes-sigs/kueue/releases/download/$VERSION/manifests.yaml
# mv manifests.yaml ./crd/kueue.yaml
kubectl apply --server-side -f ./crd/kueue.yaml
```

Note that the kueue is configured for this cluster _exactly_ and if you change it you need to change that cluster! Any resource request
that is on the job pod template is going to need to be defined in the cluster queue resources, otherwise the Job (and pods) cannot be admitted.
Then apply:

```bash
kubectl apply -f ./crd/cluster-queues.yaml
```

Then try running experiments:

```bash
time python run_experiments.py --outdir ./results/mixed/kueue --config-name mixed --batches 1 --iters 10 --kueue
```

There is more information [here](https://kueue.sigs.k8s.io/docs/tasks/run/plain_pods/) and
[here](https://kueue.sigs.k8s.io/docs/tasks/manage/setup_sequential_admission/). The user experience of Kueue is really nice! Clean up.

```bash
kubectl delete -f ./crd/cluster-queues.yaml
kubectl delete -f ./crd/kueue.yaml
```

### Fluence

We are going to follow the instructions from [the main repository](https://github.com/flux-framework/flux-k8s) to use the provided Fluence, but use a [custom branch](https://github.com/flux-framework/flux-k8s/pull/69) we are working on.  The newer version of fluence requires the certificate manager. There is likely a way to do self-signed certs but we haven't tried it yet.

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.1/cert-manager.yaml
```

I built the images and used the digests exactly as follows:

```bash
# And then install using the charts. The pull policy ensures we use the loaded ones
cd ./upstream/manifests/install/charts
helm install \
  --set scheduler.image=${REGISTRY}/fluence:latest \
  --set controller.image=${REGISTRY}/fluence-controller:latest \
  --set scheduler.sidecarimage=${REGISTRY}/fluence-sidecar:latest \
        fluence as-a-second-scheduler/
```

Ensure both scheduler pods are running (they just need to pull, etc).

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
$ kubectl logs fluence-6c777cb68d-nwt62 
```

And save metadata about nodes and fluence.

```bash
kubectl get pods -o json > results/fluence-pods.json
kubectl get nodes -o json > results/nodes.json
```

We are going to run the experiment with the largest range of sizes and different numbers of cpu

```bash
time python run_experiments.py --outdir ./results/mixed/fluence --config-name mixed --fluence --batches 1 --iters 10
```
 
Delete the fluence pods after that with helm uninstall, and then helm uninstall fluence.

```bash
helm uninstall fluence
```


### Analysis

```
python plot-schedulers.py
```

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```
