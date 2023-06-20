# KubeFlow Kind

I started deploying this on [Google Cloud](../kubeflow) but it was taking so long
I decided to use kind first. We are going to follow the [instructions here](https://www.kubeflow.org/docs/components/pipelines/v1/installation/localcluster-deployment/). First, create the kind cluster:


```bash
$ kind create cluster
```

And then deploy KubeFlow pipelines. Note that I needed a machine with a ton of memory to do this, or
my standard machine with everything closed!

```bash
# env/platform-agnostic-pns hasn't been publically released, so you will install it from master
export PIPELINE_VERSION=1.8.5
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic-pns?ref=$PIPELINE_VERSION"
```

When everything is running (see `kubectl get pods -n kubeflow`, and you'll get an error it is PENDING if not) you can
forward a port to see it running on our local machine!

```bash
$ kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

You should be able to open the Kubeflow Pipelines UI at [http://localhost:8080/](http://localhost:8080/).

When you are done:

```bash
$ kind delete cluster
```
