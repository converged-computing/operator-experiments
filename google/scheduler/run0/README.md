# Fluence vs. Default Scheduler

This is a testing setup for running an experiment to test fluence against the default scheduler.
We will use the instance type that we got working for LAMMPS previously.

 - c2d-standard-8
  
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


Old command:

```bash
GOOGLE_PROJECT=myproject
gcloud compute networks create mtu9k --mtu=8896 
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=129 \
    --region=us-central1-a \
    --project=${GOOGLE_PROJECT} \
    --machine-type=c2d-standard-112 \
    --network-performance-configs=total-egress-bandwidth-tier=TIER_1 \
    --enable-gvnic \
    --network=mtu9k \
    --system-config-from-file=./crd/system-config.yaml
```

Save metadata for nodes.

```bash
mkdir -p ./data
kubectl get nodes -o json > data/nodes.json
```


### Install the Scheduler

We are going to follow the instructions from [here](https://github.com/flux-framework/flux-k8s/tree/main#deploy) to install Fluence.

```bash
$ git clone https://github.com/openshift-psap/scheduler-plugins.git -b fluence
$ cd scheduler-plugins/manifests/install/charts
$ helm install \
  --set scheduler.image=ghcr.io/flux-framework/fluence:latest \
  --set scheduler.sidecarimage=ghcr.io/flux-framework/fluence-sidecar \
    schedscheduler-plugins as-a-second-scheduler/
```

Sanity check both pods are running (fluence and the sidecar)

```bash
$ kubectl logs -n scheduler-plugins fluence-6d87847584-k54lk 
```
```
Defaulted container "sidecar" out of: sidecar, scheduler-plugins-scheduler
This is the fluxion grpc server
Created cli context  &{}
&{}
Number nodes  4
node in flux group  gke-test-cluster-default-pool-8986df00-0j3n
Node  gke-test-cluster-default-pool-8986df00-0j3n  flux cpu  3
Node  gke-test-cluster-default-pool-8986df00-0j3n  total mem  29202693888
node in flux group  gke-test-cluster-default-pool-8986df00-fq60
Node  gke-test-cluster-default-pool-8986df00-fq60  flux cpu  3
Node  gke-test-cluster-default-pool-8986df00-fq60  total mem  29020379008
node in flux group  gke-test-cluster-default-pool-8986df00-pv8n
Node  gke-test-cluster-default-pool-8986df00-pv8n  flux cpu  3
Node  gke-test-cluster-default-pool-8986df00-pv8n  total mem  29298037248
node in flux group  gke-test-cluster-default-pool-8986df00-r90r
Node  gke-test-cluster-default-pool-8986df00-r90r  flux cpu  3
Node  gke-test-cluster-default-pool-8986df00-r90r  total mem  29207936768
Can request at most  12  exclusive cpu
Match policy:  {"matcher_policy": "lonode"}
[GRPCServer] gRPC Listening on [::]:4242
```

And you should see health checks here:

```bash
$ kubectl logs -n scheduler-plugins fluence-6d87847584-k54lk -c scheduler-plugins-scheduler 
```

The next step has us tainting nodes with the label fluence ([done here](https://github.com/flux-framework/flux-k8s/blob/e4b2dc20c095ba95a7217065349e30ee9bb34723/canopie22-artifacts/kube_setup/eks-efa-cluster-config.yaml#L34))
but I don't think we need to do that since we don't have a launcher with the flux operator (this was for the MPI operator)? Here is what the script looks like:

```bash
#!/bin/bash

for n in $( kubectl get nodes -l fluence=true | tail -n +2 | cut -d' ' -f1 ); do
    kubectl taint nodes $n worker=true:NoSchedule
done 
```

And it is [here](https://github.com/flux-framework/flux-k8s/blob/canopie22-artifacts/canopie22-artifacts/kube_setup/taint_workers.sh).

### Example Scheduling

Now let's apply the examples:

```bash
kubectl apply -f example/
```

TODO these don't work for fluence - there is some bug (?) or something weird in the logs.

```console
I1103 01:19:41.748831       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:19:41.748881       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="50.89µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:57816" resp=200
I1103 01:19:41.749269       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:19:41.749294       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="32.47µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:57814" resp=200
I1103 01:19:51.749945       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:19:51.749986       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="54.95µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:50382" resp=200
I1103 01:19:51.750204       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:19:51.750236       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="38.02µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:50396" resp=200
I1103 01:20:00.141377       1 reflector.go:536] k8s.io/client-go/informers/factory.go:134: Watch close - *v1.PersistentVolume total 7 items received
I1103 01:20:00.141470       1 round_trippers.go:466] curl -v -XGET  -H "Accept: application/vnd.kubernetes.protobuf, */*" -H "User-Agent: kube-scheduler/v0.0.0 (linux/amd64) kubernetes/$Format/scheduler" -H "Authorization: Bearer <masked>" 'https://10.12.0.1:443/api/v1/persistentvolumes?allowWatchBookmarks=true&resourceVersion=15992&timeout=7m56s&timeoutSeconds=476&watch=true'
I1103 01:20:00.143524       1 round_trippers.go:570] HTTP Statistics: GetConnection 0 ms ServerProcessing 1 ms Duration 2 ms
I1103 01:20:00.143538       1 round_trippers.go:577] Response Headers:
I1103 01:20:00.143543       1 round_trippers.go:580]     Date: Fri, 03 Nov 2023 01:20:00 GMT
I1103 01:20:00.143546       1 round_trippers.go:580]     Audit-Id: 1ea788de-ed7f-4758-aab7-aad6c7ac59eb
I1103 01:20:00.143549       1 round_trippers.go:580]     Cache-Control: no-cache, private
I1103 01:20:00.143551       1 round_trippers.go:580]     Content-Type: application/vnd.kubernetes.protobuf;stream=watch
I1103 01:20:00.143554       1 round_trippers.go:580]     X-Kubernetes-Pf-Flowschema-Uid: 44e6cfc6-d225-4b41-af8e-27fb089ba83c
I1103 01:20:00.143557       1 round_trippers.go:580]     X-Kubernetes-Pf-Prioritylevel-Uid: 0356118b-6d88-49de-8fd9-0d894d3988f0
I1103 01:20:01.749169       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:20:01.749206       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="48µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:32858" resp=200
I1103 01:20:01.749589       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:20:01.749633       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="50.82µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:32856" resp=200
I1103 01:20:11.749807       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:20:11.749856       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="77.76µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:43078" resp=200
I1103 01:20:11.749997       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:20:11.750020       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="33.14µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:43066" resp=200
I1103 01:20:15.165214       1 reflector.go:255] Listing and watching *v1beta1.CSIStorageCapacity from k8s.io/client-go/informers/factory.go:134
I1103 01:20:15.165342       1 round_trippers.go:466] curl -v -XGET  -H "Accept: application/vnd.kubernetes.protobuf, */*" -H "User-Agent: kube-scheduler/v0.0.0 (linux/amd64) kubernetes/$Format/scheduler" -H "Authorization: Bearer <masked>" 'https://10.12.0.1:443/apis/storage.k8s.io/v1beta1/csistoragecapacities?limit=500&resourceVersion=0'
I1103 01:20:15.168786       1 round_trippers.go:570] HTTP Statistics: GetConnection 0 ms ServerProcessing 3 ms Duration 3 ms
I1103 01:20:15.168797       1 round_trippers.go:577] Response Headers:
I1103 01:20:15.168801       1 round_trippers.go:580]     X-Kubernetes-Pf-Flowschema-Uid: 44e6cfc6-d225-4b41-af8e-27fb089ba83c
I1103 01:20:15.168804       1 round_trippers.go:580]     X-Kubernetes-Pf-Prioritylevel-Uid: 0356118b-6d88-49de-8fd9-0d894d3988f0
I1103 01:20:15.168807       1 round_trippers.go:580]     Content-Length: 116
I1103 01:20:15.168809       1 round_trippers.go:580]     Date: Fri, 03 Nov 2023 01:20:15 GMT
I1103 01:20:15.168812       1 round_trippers.go:580]     Audit-Id: 5f7e66a5-a87d-45c4-bce2-cbbadec93f22
I1103 01:20:15.168814       1 round_trippers.go:580]     Cache-Control: no-cache, private
I1103 01:20:15.168817       1 round_trippers.go:580]     Content-Type: application/vnd.kubernetes.protobuf
I1103 01:20:15.168832       1 request.go:1179] Response Body:
00000000  6b 38 73 00 0a 0c 0a 02  76 31 12 06 53 74 61 74  |k8s.....v1..Stat|
00000010  75 73 12 5c 0a 06 0a 00  12 00 1a 00 12 07 46 61  |us.\..........Fa|
00000020  69 6c 75 72 65 1a 30 74  68 65 20 73 65 72 76 65  |ilure.0the serve|
00000030  72 20 63 6f 75 6c 64 20  6e 6f 74 20 66 69 6e 64  |r could not find|
00000040  20 74 68 65 20 72 65 71  75 65 73 74 65 64 20 72  | the requested r|
00000050  65 73 6f 75 72 63 65 22  08 4e 6f 74 46 6f 75 6e  |esource".NotFoun|
00000060  64 2a 0a 0a 00 12 00 1a  00 28 00 32 00 30 94 03  |d*.......(.2.0..|
00000070  1a 00 22 00                                       |..".|
W1103 01:20:15.168896       1 reflector.go:324] k8s.io/client-go/informers/factory.go:134: failed to list *v1beta1.CSIStorageCapacity: the server could not find the requested resource
E1103 01:20:15.168908       1 reflector.go:138] k8s.io/client-go/informers/factory.go:134: Failed to watch *v1beta1.CSIStorageCapacity: failed to list *v1beta1.CSIStorageCapacity: the server could not find the requested resource
I1103 01:20:21.749622       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:20:21.749667       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="59.73µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:43390" resp=200
I1103 01:20:21.749897       1 pathrecorder.go:240] kube-scheduler: "/healthz" satisfied by exact match
I1103 01:20:21.749926       1 httplog.go:129] "HTTP" verb="GET" URI="/healthz" latency="33.51µs" userAgent="kube-probe/1.27" audit-ID="" srcIP="10.8.2.1:43392" resp=200
I1103 01:20:24.145535       1 reflector.go:536] k8s.io/client-go/informers/factory.go:134: Watch close - *v1.PodDisruptionBudget total 7 items received
I1103 01:20:24.145649       1 round_trippers.go:466] curl -v -XGET  -H "Accept: application/vnd.kubernetes.protobuf, */*" -H "User-Agent: kube-scheduler/v0.0.0 (linux/amd64) kubernetes/$Format/scheduler" -H "Authorization: Bearer <masked>" 'https://10.12.0.1:443/apis/policy/v1/poddisruptionbudgets?allowWatchBookmarks=true&resourceVersion=16205&timeout=7m16s&timeoutSeconds=436&watch=true'
I1103 01:20:24.147146       1 round_trippers.go:570] HTTP Statistics: GetConnection 0 ms ServerProcessing 1 ms Duration 1 ms
I1103 01:20:24.147159       1 round_trippers.go:577] Response Headers:
I1103 01:20:24.147163       1 round_trippers.go:580]     X-Kubernetes-Pf-Flowschema-Uid: 44e6cfc6-d225-4b41-af8e-27fb089ba83c
I1103 01:20:24.147166       1 round_trippers.go:580]     X-Kubernetes-Pf-Prioritylevel-Uid: 0356118b-6d88-49de-8fd9-0d894d3988f0
I1103 01:20:24.147169       1 round_trippers.go:580]     Date: Fri, 03 Nov 2023 01:20:24 GMT
I1103 01:20:24.147172       1 round_trippers.go:580]     Audit-Id: 8a43d556-5fef-49c4-94cc-640644cd2d68
I1103 01:20:24.147174       1 round_trippers.go:580]     Cache-Control: no-cache, private
I1103 01:20:24.147177       1 round_trippers.go:580]     Content-Type: application/vnd.kubernetes.protobuf;stream=watch
```

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a --quiet
```
