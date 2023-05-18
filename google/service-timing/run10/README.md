# Service Timing

For this experiment we will bring up the smallest "largest" cluster that
can reproduce the leader broker and followers never connecting.
I found this to be a size 32 cluster (16 connected).

### Setup


```console
gcloud container clusters create flux-cluster \
   --region=us-central1-a --project $GOOGLE_PROJECT \
   --machine-type c2d-standard-112 --num-nodes=32 \
   --cluster-dns=clouddns --cluster-dns-scope=cluster \
   --tags=flux-cluster  --enable-dataplane-v2 \
   --threads-per-core=1
```

Then create the namespace and install the operator.

```bash
kubectl create namespace flux-operator
kubectl apply -f operator/flux-operator.yaml
```

You can check the pod logs in the `operator-system` namespace to ensure it is running!
Save the nodes if you desire (I [saved mine, FYI](operator/vnodes.json) if you want to compare)

```bash
kubectl get nodes -o json > operator/vnodes.json
```

Then create the MiniCluster. This cluster is started in interactive mode,
so it should wire up and then allow you to connect. However at this scale,
in my testing, it's never able to.

```bash
kubectl apply -f operator/minicluster-32.yaml
```

Wait until the containers are running (it takes about a minute for pull)

```bash
$ kubectl get pods -n flux-operator 
```

If you look at flux-sample-0-* (the leader broker) you will see it connected (but waiting for workers)

```
broker.info[0]: rc1-success: init->quorum 0.252631s
broker.info[0]: online: flux-sample-0 (ranks 0)
broker.err[0]: quorum delayed: waiting for flux-sample-[1-15] (rank 1-15)
broker.err[0]: quorum delayed: waiting for flux-sample-[1-15] (rank 1-15)
broker.err[0]: quorum delayed: waiting for flux-sample-[1-15] (rank 1-15)
```

And if you look at any worker, it will not be able to connect:

```
🌀  flux start -o --config /etc/flux/config -Scron.directory=/etc/flux/system/cron.d   -Stbon.fanout=256   -Srundir=/run/flux -Sbroker.rc2_none    -Sstatedir=/var/lib/flux   -Slocal-uri=local:///run/flux/local   -Stbon.zmqdebug=1  -Slog-stderr-level=6    -Slog-stderr-mode=local
broker.err[1]: Warning: unable to resolve upstream peer flux-sample-0.flux-service.flux-operator.svc.cluster.local: Name or service not known
broker.info[1]: start: none->join 0.32007ms
```

There *should* be a message about joining the parent (but it won't show up).
In this state you wouldn't be able to use Flux, although you can shell into a pod and look around!
If you DO see it connect, try just making the cluster bigger, and be sure to update
the MiniCluster CRD tasks to be 56 * nodes.

When you are done - clean up!

```bash
$ gcloud container clusters delete flux-cluster
```
