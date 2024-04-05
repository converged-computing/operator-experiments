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
 
For experiment prototyping see [run7](../run7).
 

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

Now let's install the Flux Operator. We have a manifest saved with an exact digest:

```bash
kubectl apply -f ./crd/flux-operator.yaml
```

You can check logs to ensure it is also running, in the `operator-system` namespace.

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
mkdir -p ./results
kubectl logs fluence-757fdcd854-cbqn2 
```
```console
Defaulted container "sidecar" out of: sidecar, scheduler-plugins-scheduler
This is the fluxion grpc server
I0404 23:04:27.488387       1 fluxion.go:26] [Fluence] Created flux resource client &{%!s(*fluxcli.ReapiCtx=&{})}
Number nodes  8

📦️ gke-test-cluster-default-pool-a6471b43-6bws
      allocated cpu: 1
      allocated mem: 631591168
      available cpu: 3
       running pods: 9
      available mem: 29152308992

📦️ gke-test-cluster-default-pool-a6471b43-82sj
      allocated cpu: 1
      allocated mem: 454458880
      available cpu: 3
       running pods: 6
      available mem: 29329441280

📦️ gke-test-cluster-default-pool-a6471b43-nn21
      allocated cpu: 1
      allocated mem: 465916160
      available cpu: 3
       running pods: 7
      available mem: 29317975808

📦️ gke-test-cluster-default-pool-a6471b43-phfd
      allocated cpu: 1
      allocated mem: 581259520
      available cpu: 3
       running pods: 7
      available mem: 29202640640

📦️ gke-test-cluster-default-pool-a6471b43-wjgz
      allocated cpu: 1
      allocated mem: 465916160
      available cpu: 3
       running pods: 7
      available mem: 29317984000

📦️ gke-test-cluster-default-pool-a6471b43-wql0
      allocated cpu: 1
      allocated mem: 565530880
      available cpu: 3
       running pods: 7
      available mem: 29218369280

📦️ gke-test-cluster-default-pool-a6471b43-xwh3
      allocated cpu: 1
      allocated mem: 763574400
      available cpu: 3
       running pods: 13
      available mem: 29020325760

📦️ gke-test-cluster-default-pool-a6471b43-zzwn
      allocated cpu: 1
      allocated mem: 434458880
      available cpu: 3
       running pods: 6
      available mem: 29349441280

I0404 23:04:27.748188       1 fluxion.go:41] [Fluence] match policy: {"matcher_policy": "lonode"}
Can request at most 24 exclusive cpu[GRPCServer] gRPC Listening on [::]:4242
```

And save metadata about nodes and fluence.

```bash
mkdir -p results
kubectl get pods -o json > results/fluence-pods.json
kubectl get nodes -o json > results/nodes.json
```

### Experiment Prototyping

Ensure you have the same requirements installed.

```bash
pip install -r requirements.txt
```

#### Pull Container

Note that I made an indexed job to run on all nodes just to pull containers before running anything. It probably doesn't matter what scheduler we use here to do this, we just need to load the lammps container to the nodes.

```bash
kubectl apply -f crd/pull-container.yaml
kubectl delete -f crd/pull-container.yaml
```

We are going to run the experiment with the largest range of sizes and different numbers of cpu

```bash
# 2,3,4,5,6 then 2 (1 cpu), 3/4/5/6 (2 cpu)
mkdir -p ./results/lammps-mixed
time python run_experiments.py --outdir ./results/lammps-mixed/fluence --config-name lammps-mixed --fluence --batches 1 --iters 20
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

### Default Scheduler

Now we can use the default scheduler. We can run the same experiment, but without the `--fluence` flag.

```bash
time python run_experiments.py --outdir ./results/lammps-mixed/kube-sched --config-name lammps-mixed --batches 1 --iters 20
```

It will clog sooner or later. Save the current stage.

```bash
kubectl get pods -o json > ./results/default-clogged-pods.json
```

```
$ kubectl get pods | grep Pending | wc -l
345
(env) vanessa@vanessa-ThinkPad-T14-Gen-4:/tmp/flux-core/src/bindings/python/flux$ kubectl get pods | grep Running | wc -l
8
(env) vanessa@vanessa-ThinkPad-T14-Gen-4:/tmp/flux-core/src/bindings/python/flux$ kubectl get pods | grep Init | wc -l
0
```

Cancel the experiment and clean up.

```bash
kubectl delete miniclusters --all
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


### Kueue 

```console
# This is how I got the original one
# VERSION=v0.6.1
# wget https://github.com/kubernetes-sigs/kueue/releases/download/$VERSION/manifests.yaml
# mv manifests.yaml ./crd/kueue.yaml
kubectl delete -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.1/cert-manager.yaml
kubectl apply --server-side -f ./crd/kueue.yaml
```
```bash
time python run_experiments.py --outdir ./results/lammps-mixed/kueue --config-name lammps-mixed --batches 1 --iters 20 --kueue
```

It never worked:

```
{"level":"info","ts":"2024-04-05T04:02:52.340470685Z","caller":"controller/controller.go:220","msg":"Starting workers","controller":"resourceflavor","controllerGroup":"kueue.x-k8s.io","controllerKind":"ResourceFlavor","worker count":1}
{"level":"info","ts":"2024-04-05T04:02:52.346684735Z","caller":"controller/controller.go:220","msg":"Starting workers","controller":"localqueue","controllerGroup":"kueue.x-k8s.io","controllerKind":"LocalQueue","worker count":1}
{"level":"info","ts":"2024-04-05T04:02:52.346719165Z","caller":"controller/controller.go:220","msg":"Starting workers","controller":"v1_pod","worker count":5}
{"level":"info","ts":"2024-04-05T04:02:52.347140595Z","caller":"controller/controller.go:220","msg":"Starting workers","controller":"workload","controllerGroup":"kueue.x-k8s.io","controllerKind":"Workload","worker count":5}
2024/04/05 04:03:02 http: TLS handshake error from 10.48.4.2:57628: EOF
2024/04/05 04:03:03 http: TLS handshake error from 10.48.0.3:35068: EOF
2024/04/05 04:03:03 http: TLS handshake error from 10.48.2.2:38276: EOF
2024/04/05 04:03:06 http: TLS handshake error from 10.48.1.2:50810: EOF
2024/04/05 04:03:06 http: TLS handshake error from 10.48.1.2:50820: EOF
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
