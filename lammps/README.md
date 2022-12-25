# Lammps on Google Kubernetes Engine

In this short experiment we will run the Flux Operator on Google Cloud, at first
at a very small size intended for development. 

## Install

You should first [install gcloud](https://cloud.google.com/sdk/docs/quickstarts) 
and ensure you are logged in and have kubectl installed:

```bash
$ gcloud auth login
```

Depending on your install, you can either install with gcloud:

```bash
$ gcloud components install kubectl
```
or just [on your own](https://kubernetes.io/docs/tasks/tools/).


## Create Cluster

Now let's use gcloud to create a cluster, and we are purposefully going to choose
a very small node type to test. Note that I choose us-central1-a because it tends
to be cheaper (and closer to me).

```bash
$ gcloud container clusters create lammps-cluster --project <project name> --zone us-central1-a --cluster-version 1.23 --machine-type n1-standard-1 --num-nodes=4
```

In your Google cloud interface, you should be able to see the cluster! Note
this might take a few minutes.

![img/cluster.png](img/cluster.png)

I also chose a tiny one anticipating having it up longer to figure things out.

## Get Credentials

Next we need to ensure that we can issue commands to our cluster with kubectl.
To get credentials, in the view shown above, select the cluster and click "connect."
Doing so will show you the correct statement to run to configure command-line access,
which probably looks something like this:

```bash
$ gcloud container clusters get-credentials lammps-cluster --zone us-central1-a --project <project name>
```
```console
Fetching cluster endpoint and auth data.
kubeconfig entry generated for lammps-cluster.
```

Finally, use [cloud IAM](https://cloud.google.com/iam) to ensure you can create roles, etc.

```bash
$ kubectl create clusterrolebinding cluster-admin-binding --clusterrole cluster-admin --user $(gcloud config get-value core/account)
```
```console
clusterrolebinding.rbac.authorization.k8s.io/cluster-admin-binding created
```

At this point you should be able to get your nodes:

```bash
$ kubectl get nodes
```
```console
NAME                                            STATUS   ROLES    AGE     VERSION
gke-lammps-cluster-default-pool-f103d9d8-379m   Ready    <none>   3m41s   v1.23.14-gke.1800
gke-lammps-cluster-default-pool-f103d9d8-3wf9   Ready    <none>   3m42s   v1.23.14-gke.1800
gke-lammps-cluster-default-pool-f103d9d8-c174   Ready    <none>   3m42s   v1.23.14-gke.1800
gke-lammps-cluster-default-pool-f103d9d8-zz1q   Ready    <none>   3m42s   v1.23.14-gke.1800
```

## Deploy Operator 

To deploy the Flux Operator, here is how to do it directly from the codebase:

```bash
$ git clone https://github.com/flux-framework/flux-operator
$ cd flux-operator
```

A deploy will use the latest docker image [from the repository](https://github.com/orgs/flux-framework/packages?repo_name=flux-operator):

```bash
$ make deploy
```
```console
...
clusterrole.rbac.authorization.k8s.io/operator-manager-role created
clusterrole.rbac.authorization.k8s.io/operator-metrics-reader created
clusterrole.rbac.authorization.k8s.io/operator-proxy-role created
rolebinding.rbac.authorization.k8s.io/operator-leader-election-rolebinding created
clusterrolebinding.rbac.authorization.k8s.io/operator-manager-rolebinding created
clusterrolebinding.rbac.authorization.k8s.io/operator-proxy-rolebinding created
configmap/operator-manager-config created
service/operator-controller-manager-metrics-service created
deployment.apps/operator-controller-manager created
```

Ensure the `operator-system` namespace was created:

```bash
$ kubectl get namespace
NAME              STATUS   AGE
default           Active   6m39s
kube-node-lease   Active   6m42s
kube-public       Active   6m42s
kube-system       Active   6m42s
operator-system   Active   39s
```
```bash
$ kubectl describe namespace operator-system
Name:         operator-system
Labels:       control-plane=controller-manager
              kubernetes.io/metadata.name=operator-system
Annotations:  <none>
Status:       Active

Resource Quotas
  Name:                              gke-resource-quotas
  Resource                           Used  Hard
  --------                           ---   ---
  count/ingresses.extensions         0     100
  count/ingresses.networking.k8s.io  0     100
  count/jobs.batch                   0     5k
  pods                               1     1500
  services                           1     500

No LimitRange resource.
```

And you can find the name of the operator pod as follows:

```bash
$ kubectl get pod --all-namespaces
```
```console
      <none>
operator-system   operator-controller-manager-56b5bcf9fd-m8wg4               2/2     Running   0          73s
```

Make your namespace for the flux-operator custom resource definition (CRD):

```bash
$ kubectl create namespace flux-operator
```

Now let's apply the custom resource definition to create the lammps mini cluster!

```bash
$ kubectl apply -f minicluster-lammps.yaml 
```

Now we can get logs for the manager to see what is going on:

```bash
$ kubectl logs -n operator-system operator-controller-manager-56b5bcf9fd-m8wg4 
```

And different ways to see logs for pods:

```bash
$ kubectl -n flux-operator describe pods flux-sample-0-742bm

# See pods running and state
$ kubectl get -n flux-operator pods

# Add the -f to keep it hanging
$ kubectl -n flux-operator logs flux-sample-0-742bm -f
```
To shell into a pod to look around (noting where important flux stuff is)

```bash
$ kubectl exec --stdin --tty -n flux-operator flux-sample-0-742bm -- /bin/bash
```
```console
ls /mnt/curve
ls /etc/flux
ls /etc/flux/config
```

If you need to run in verbose (non-test) mode, set test to false in the [minicluster-lammps.yaml](minicluster-lammps.yaml).
And make sure to clean up first:

```bash
$ kubectl delete -f minicluster-lammps.yaml
```

and wait until the pods are gone:

```bash
$ kubectl get -n flux-operator pods
No resources found in flux-operator namespace.
```

**STOPPED HERE** Note that a shared key doesn't seem to be created, possibly because
the shared volume isn't created - even after manually copying it I don't see it in
the worker node. And in the logs:

```
🤓 MiniCluster.DeadlineSeconds 31500000
🤓 MiniCluster.Size 4
🤓 MiniCluster.Container.0.Image ghcr.io/rse-ops/lammps:flux-sched-focal-v0.24.0
🤓 MiniCluster.Container.0.Command lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
🤓 MiniCluster.Container.0.FluxRunner true
 🪵 Unable to write data into the file
 🪵 Unable to write data into the file
 🪵 Unable to write data into the file
```

## Clean up

Make sure you clean everything up! You can delete the lammps deploy first:

```bash
$ kubectl delete -f minicluster-lammps.yaml
```

And then undeploy the operator (this is again at the root of the operator repository clone)

```bash
$ make undeploy
```

And then to delete the cluster with gcloud:

```bash
$ gcloud container clusters delete --zone us-central1-a lammps-cluster
```

I like to check in the cloud console to ensure that it was actually deleted.
