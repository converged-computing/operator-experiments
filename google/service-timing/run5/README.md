# Service Timing

For this experiment we want to try a test branch of the operator (hash / digest in the
flux-operator.yaml) that eliminates DNS by writing the hostnames into `/etc/hosts`
You can see the original runs in [run1](../run1)

### Setup

```console
gcloud container clusters create flux-operator \
   --region=us-central1-a --project $GOOGLE_PROJECT \
   --machine-type n1-standard-2 --num-nodes=4 \
   --tags=flux-cluster  --enable-dataplane-v2

$ kubectl create namespace flux-operator
```

### Hostnames on Current Networking

First let's apply the current design (with wrap added) so we can save pods (and see hostnames)

```
$ kubectl create namespace flux-operator
$ kubectl apply -f current/flux-operator-dev.yaml
$ kubectl apply -f current/minicluster.yaml
```

Wait for the pods to be running, then save logs and pods:

```
$ kubectl logs -n flux-operator flux-sample-0-bfmll -f > current/flux-sample-0.log
# do for each of 1,2,3 too
$ kubectl get pods -n flux-operator -o json > current/pods.json
$ kubectl get nodes -o json > current/nodes.json
```

And inspect hostnames:

```
$ kubectl get pods -n flux-operator -o yaml | grep hostname
    hostname: flux-sample-0
    hostname: flux-sample-1
    hostname: flux-sample-2
    hostname: flux-sample-3
```

And run the programmatic portion:

```bash
python time-minicluster.py current
```

Then you should be able to delete the operator (and the MiniCluster goes with it).

```bash
$ kubectl delete -f current/flux-operator-dev.yaml
```

### No DNS

The new design can [be seen here]() - this isn't intended to be merged, but just
for this experiment. As an example of the config map it generates (that will be used
to update the `/etc/hosts`:

```
$ kubectl apply -f no-dns/flux-operator-dev.yaml
$ kubectl apply -f no-dns/minicluster.yaml
```

Wait for the pods to be running, then save logs and pods:

```
$ kubectl logs -n flux-operator flux-sample-0-bfmll -f > ./no-dns/flux-sample-0.log
# do for each of 1,2,3 too
$ kubectl get pods -n flux-operator -o json > no-dns/pods.json
```

```
$ kubectl get pods -n flux-operator -o yaml | grep hostname
    hostname: flux-sample-0
    hostname: flux-sample-1
    hostname: flux-sample-2
    hostname: flux-sample-3
```

And delete

```bash
$ kubectl delete -f ./no-dns/minicluster.yaml
```

Run programatically:

```bash
python time-minicluster.py no-dns
```

Don't forget to clean up!

```bash
$ gcloud container clusters delete flux-operator
```

#### Compare Flux Start Times

Now we want to compare the same above, but programatically across runs.



