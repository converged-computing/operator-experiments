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
3. If/ when a scheduler setup clogs (and the queue stops moving)
 
For experiment prototyping see [run8](../run8).
 
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
time python run_experiments.py --outdir ./results/mixed/kube-sched --config-name mixed --batches 1 --iters 20
```

It will clog sooner or later. This run it clogged around 5 minutes, here is the state to see it's not moving:

```console
$ kubectl get pods | grep Running
job-0-0-size-5-0-q72b8    1/1     Running   0          9m30s
job-0-1-size-6-0-pctb2    1/1     Running   0          9m27s
job-0-1-size-6-2-6jznd    1/1     Running   0          9m27s
job-0-15-size-5-4-z859k   1/1     Running   0          8m38s
job-0-3-size-4-3-gch6d    1/1     Running   0          9m21s
job-0-4-size-4-1-5z5js    1/1     Running   0          9m18s
job-0-8-size-5-1-9tvbh    1/1     Running   0          9m3s
job-0-8-size-5-4-jtzvv    1/1     Running   0          9m3s
```

In the above set, we only have one leader that is timing (the rest are sleeping without leader).
In the main terminal or logs you'll see it constantly trying the same pod - it won't ever come online.

```bash
Failed to ping pod job-0-0-size-3-1.s003, retrying in 1 second...
```

Save the state of the pods

```bash
kubectl get pods -o json > ./results/default-clogged-pods.json
```

```bash
$ kubectl get pods | grep Pending | wc -l
345
$ kubectl get pods | grep Running | wc -l
8
```

Cancel the experiment and clean up.

```bash
kubectl delete jobs --all
kubectl delete service --all
```

### Kueue 

I'm trying Kueue first this time, before installing the cert manager, because I suspect that was related to the bug.

```console
# This is how I got the original one
# VERSION=v0.6.1
# wget https://github.com/kubernetes-sigs/kueue/releases/download/$VERSION/manifests.yaml
# mv manifests.yaml ./crd/kueue.yaml
kubectl apply --server-side -f ./crd/kueue.yaml

kubectl apply -f ./crd/cluster-queue.yaml
kubectl apply -f ./crd/resource-flavor.yaml
kubectl apply -f ./crd/user-queue.yaml
```

Got slightly closer this time! I created the above (and was able to at least get around TLS) but likely a config is wrong
somewhere. See "Configuration" in the kueue.yaml compared to the pod labels I'm applying.

```bash
time python run_experiments.py --outdir ./results/mixed/kueue --config-name mixed --batches 1 --iters 20 --kueue
```

Note that it will run, but won't use kueue (defeats the purpose)
When you are done:

```bash
kubectl delete -f ./crd/cluster-queue.yaml
kubectl delete -f ./crd/resource-flavor.yaml
kubectl delete -f ./crd/user-queue.yaml
kubectl delete -f ./crd/kueue.yaml
```

### Install Cert Manager

The newer version of fluence requires the certificate manager. There is likely a way to do self-signed certs but we haven't tried it yet.

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.1/cert-manager.yaml
```

### Fluence

We are going to follow the instructions from [the main repository](https://github.com/flux-framework/flux-k8s) to use the provided Fluence, but use a [custom branch](https://github.com/flux-framework/flux-k8s/pull/69) we are working on. I built the images and used the digests exactly as follows:

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
Defaulted container "sidecar" out of: sidecar, scheduler-plugins-scheduler
This is the fluxion grpc server
I0411 16:56:13.922017       1 fluxion.go:26] [Fluence] Created flux resource client &{%!s(*fluxcli.ReapiCtx=&{})}
Number nodes  8

📦️ gke-test-cluster-default-pool-be3a8627-13j6
      allocated cpu: 1
      allocated mem: 522616320
      available cpu: 3
       running pods: 9
      available mem: 29261283840

📦️ gke-test-cluster-default-pool-be3a8627-2wlv
      allocated cpu: 1
      allocated mem: 800274560
      available cpu: 3
       running pods: 15
      available mem: 28983625600

📦️ gke-test-cluster-default-pool-be3a8627-bv4m
      allocated cpu: 1
      allocated mem: 502616320
      available cpu: 3
       running pods: 9
      available mem: 29281283840

📦️ gke-test-cluster-default-pool-be3a8627-k99l
      allocated cpu: 1
      allocated mem: 502616320
      available cpu: 3
       running pods: 9
      available mem: 29281275648

📦️ gke-test-cluster-default-pool-be3a8627-mnkm
      allocated cpu: 1
      allocated mem: 633688320
      available cpu: 3
       running pods: 10
      available mem: 29150211840

📦️ gke-test-cluster-default-pool-be3a8627-t8vv
      allocated cpu: 1
      allocated mem: 471159040
      available cpu: 3
       running pods: 8
      available mem: 29312732928

📦️ gke-test-cluster-default-pool-be3a8627-w20f
      allocated cpu: 1
      allocated mem: 502616320
      available cpu: 3
       running pods: 9
      available mem: 29281283840

📦️ gke-test-cluster-default-pool-be3a8627-zs8f
      allocated cpu: 1
      allocated mem: 586502400
      available cpu: 3
       running pods: 8
      available mem: 29197397760

I0411 16:56:14.257308       1 fluxion.go:41] [Fluence] match policy: {"matcher_policy": "lonode"}
Can request at most 24 exclusive cpu[GRPCServer] gRPC Listening on [::]:4242
```

And save metadata about nodes and fluence.

```bash
mkdir -p results
kubectl get pods -o json > results/fluence-pods.json
kubectl get nodes -o json > results/nodes.json
```

We are going to run the experiment with the largest range of sizes and different numbers of cpu

```bash
time python run_experiments.py --outdir ./results/mixed/fluence --config-name mixed --fluence --batches 1 --iters 20
```
 
During running I also saved all pods:

```bash
kubectl get pods -o json > ./results/fluence-all-pods.json
```
And then finished

```bash
kubectl get pods -o json > ./results/fluence-completed-pods.json
```

Delete the fluence pods after that with helm uninstall, and then helm uninstall fluence.

```bash
helm uninstall fluence
```

### Coscheduling

```bash
git clone https://github.com/kubernetes-sigs/scheduler-plugins
cd scheduler-plugins/manifests/install/charts/as-a-second-scheduler
helm install coscheduling as-a-second-scheduler/
```

Note this installs coscheduling et al as `scheduler-plugins-scheduler`

```bash
time python run_experiments.py --outdir ./results/lammps-mixed/coscheduling --config-name lammps-mixed --batches 1 --iters 20 --coscheduling
```

Note that it clogs!

```bash
kubectl get pods -o json > ./results/coscheduling-1-clogged-pods.json
```

Delete and try installing with the config in [crd/coscheduling.yaml](crd/coscheduling.yaml).

```
kubectl delete miniclusters --all
kubectl delete podgroups --all
helm uninstall coscheduling
```

I wound up using this for the configmap.yaml template:

```yaml
{{- if .Values.plugins.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: scheduler-config
  namespace: {{ .Release.Namespace }}
data:
  scheduler-config.yaml: |
    apiVersion: kubescheduler.config.k8s.io/v1
    kind: KubeSchedulerConfiguration
    leaderElection:
      leaderElect: {{ .Values.scheduler.leaderElect }}
    profiles:
    # Compose all plugins in one profile
    - schedulerName: {{ .Values.scheduler.name }}
      plugins:
        multiPoint:
          enabled:
          - name: Coscheduling
        queueSort:
          enabled:
          - name: Coscheduling
          disabled:
          - name: "*"
      {{- if $.Values.pluginConfig }}
      pluginConfig: {{ toYaml $.Values.pluginConfig | nindent 6 }}
      {{- end }}
  {{- /* TODO: wire CRD installation with enabled plugins. */}}
{{- end }}
```

And you see:

```
s$ kubectl describe cm scheduler-config 
Name:         scheduler-config
Namespace:    default
Labels:       app.kubernetes.io/managed-by=Helm
Annotations:  meta.helm.sh/release-name: coscheduling
              meta.helm.sh/release-namespace: default

Data
====
scheduler-config.yaml:
----
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
leaderElection:
  leaderElect: false
profiles:
# Compose all plugins in one profile
- schedulerName: scheduler-plugins-scheduler
  plugins:
    multiPoint:
      enabled:
      - name: Coscheduling
    queueSort:
      enabled:
      - name: Coscheduling
      disabled:
      - name: "*"
  pluginConfig: 
  - args:
      permitWaitingTimeSeconds: 10
    name: Coscheduling


BinaryData
====

Events:  <none>
```

And then again:

```bash
time python run_experiments.py --outdir ./results/lammps-mixed/coscheduling-only --config-name lammps-mixed --batches 1 --iters 20 --coscheduling
```

It froze

```bash
kubectl get pods -o json > ./results/coscheduling-2-clogged-pods.json
helm uninstall coscheduling
```


### Analysis

```
python plot-lammps.py
```
```console
scheduler     experiment  
coscheduling  size-2-2-2-2    53.928729
              size-3-2-2-2      3.83098
              size-4-2-2-2    13.949011
              size-5-2-2-2    10.058261
default       size-2-2-2-2    83.771192
              size-3-2-2-2    30.501831
              size-4-2-2-2    44.728875
fluence       size-2-2-2-2    36.072507
              size-3-2-2-2    26.927059
              size-4-2-2-2    21.665824
              size-5-2-2-2    23.640751
              size-6-2-2-2    29.867044
Name: total_time, dtype: object
scheduler     experiment  
coscheduling  size-2-2-2-2    30.544364
              size-3-2-2-2     1.042152
              size-4-2-2-2     2.257874
              size-5-2-2-2          NaN
default       size-2-2-2-2    78.296599
              size-3-2-2-2          NaN
              size-4-2-2-2          NaN
fluence       size-2-2-2-2    26.133976
              size-3-2-2-2    40.233534
              size-4-2-2-2     7.927240
              size-5-2-2-2    12.581147
              size-6-2-2-2    13.662106
Name: total_time, dtype: float64
fluence: 100
default: 22
cosched: 7
```

Results are in [img](img). Since the default clogged, coscheduling stopped working, and kueue didn't work, we can't say much from this, but we can compare the 100 jobs from fluence to the 22 default sched. General patterns I see:

- There is a tradeoff between "run it quickly" and "run it right." The default scheduler ran some jobs quickly, but at the expense of poor scheduling that led to clogging. Fluence took its time and completed all jobs, at the cost of waiting longer for each one (logically).
- I don't know why there would be difference in lammps runtimes aside from just having too small a sample


### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```
