# Adding MPI Operator

This run will bring up one cluster that will run both the MPI operator
and Flux operator, that way we can compare the two fairly. Since we won't
add the mpi-operator to flux-cloud, we will run the creation commands manually.

## Usage

### MPI Operator Experiments

First (after exporting your AWS credentials to the environment) create the cluster that will be used by the Flux Operator and MPI
Operator.

```bash
$ eksctl create cluster -f ./scripts/kube_setup/eks-efa-cluster-config.yaml
```

You'll need [the amazon command line client](https://aws.amazon.com/cli/) and [eksctl](https://eksctl.io/).
Be weary of [this bug](https://github.com/weaveworks/eksctl/issues/6222) (I had to compile my own eksctl with the fixed config).
Next, install the mpi-operator.

```bash
$ kubectl create -f ./scripts/kube_setup/mpi-operator.yaml
```
Note that this yaml file references the MPI Operator container built with our improvements that fix race conditions.
We need to tweak the aws-efa-k8s-* pods to have a tolerance so they don't scheduler jobs. These pods are created
[by eksctl](https://github.com/weaveworks/eksctl/blob/9e0d41a8ee48d3a9ff7137dbd2aa706ac23c0bb9/pkg/addons/assets/efa-device-plugin.yaml#L5) so we are just updating them.

```bash
$ kubectl apply -f ./scripts/kube_setup/efa-device-plugin.yaml 
```

This daemonset makes the devices available to EKS pods, and we start on all nodes (including the launcher).
Next, apply a taint to worker nodes which corresponds to the toleration set in each worker pod manifest. This forces the launcher pods to run only on the launcher node(s).

```bash
$ /bin/bash ./scripts/taint_workers.sh
```

Next, let's install what we need to run experiments! This will install deps for the MPI operator and Flux operator (flux-cloud)

```bash
$ python -m venv env
$ source env/bin/activate
$ pip3 install -r requirements.txt
```

The directory [mpi-operator](mpi-operator) has scripts and config files to run experiments.

```bash
$ cd mpi-operator
```

The file `app-experiment-config.json` should just have lammps, and has all the sizes of experiments. We need the number of nodes +1 for the launcher.

Use it from the mpi-operator directory to run the experiment:

```bash
$ mkdir -p logs
$ python ./run_experiments.py --app_config ./app-experiment-config.json --node_cpu 94 --node_mem 340 --num_runs 20 --cluster_log cluster.log
```

**Note**: You should have a way to pull the containers to the nodes first, either via ssh, or via messing up experiments and re-creating everything (but having the containers pulled, possibly a more expensive way to go about it!)

You likely want to do the number of runs to correspond with the number the flux operator is doing (1 for testing, eventually 20).
Depending on the size of your cluster and available nodes configuration, these parameters need to change.

Clean up the mpi operator to prepare for the Flux Operator experiments (and note we do not bring down the cluster, we will
use the same cluster).

```bash
$ cd ../
$ kubectl delete -f ./scripts/kube_setup/mpi-operator.yaml
```

Note that we need to remove the taint on the workers.

```bash
$ /bin/bash ./scripts/untaint_workers.sh
```

I like to do one final sanity check that everything is cleaned up:

```bash
$ kubectl get pods
No resources found in default namespace.

$ kubectl get pods -n mpi-operator
No resources found in mpi-operator namespace.
```

### Flux Operator Experiments

Now install the flux operator!

```bash
$ kubectl apply -f ./scripts/kube_setup/flux-operator.yaml
```

The cluster is already up, so let's just run the jobs.

```bash
$ flux-cloud --debug apply --cloud aws
```

And that's it! See how much easier the flux operator is? If we used flux-cloud up/down we wouldn't need to manually run the up/down either!

### Clean Up

Delete the cluster with eksctl

```bash
$ eksctl delete cluster -f ./scripts/kube_setup/eks-efa-cluster-config.yaml
```
