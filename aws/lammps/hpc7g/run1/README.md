# Sanity Testing

This run will bring up one cluster for the new instance type, and one cluster
with a previously used hpc6a instance. We can't fairly compare two different clusters,
but I guess we are going to do that anyway :)

 - For the vanilla version, we use the base container `ghcr.io/rse-ops/spack-ubuntu-libfabric-ssh:ubuntu-20.04`
 - For the new instance type hpc7g we use the equivalent built with arm ` ghcr.io/rse-ops/flux-arm-lammps:june-2023-arm64`
 - All instructions are in this README, and config files / parsing scripts included for reproducibility.
 - We can't compare the nodes directly (different cores) so we bring up clusters of different sizes, but with matched cores.
 - I've updated to Kubernetes 1.27 because 1.23 is a bit old at this point.

For the last point, this means 8 nodes for the hpc6a and 12 nodes for the hpc7g (see table below for details).

- **Pricing** At the time of this writing, the cost for the hpc7g is ~$1.60/hour, so a cluster of size 8 will be $12.80/hour.
I can't find the hpc6a prices (even in cloud-select API data) but I'm going to assume similar, so a size 12 cluster
will be just a hair under $20. TLDR: I don't think I'm too concerned about prices, unless I accidentally left something
on, which I _will not do_!

Note that the design here is different than our initial one that brought up a different MiniCluster each time.
For these runs, we are going to bring up ONE cluster and then run lammps jobs on it many times,
and then save the output from Flux. This is because we care more about the use
case of running the jobs (and less about bringing up the cluster, assuming that we generally
will bring up a cluster to run more than one job!)

## TLDR

If you don't want to read further, these are the results:

- **still a work in progress!**
- I wonder if the EFA daemonset needs to be built for ARM too?

And I think we likely should rebuild both containers (arm and the other) to use
a newer version of spack, specifically targeting a commit with newer versions of
flux, etc. I already rebuilt the original (flux 0.44.0 -> 0.49.0) and can redo
the ARM images this week.

## Setup

My original EFA devices were not deployed, so I tried deploying a new `eksctl` (brave I know).
I was originally using a custom version that tweaked the permissions of the container, but I am
going to assume they have fixed this.

```bash
ARCH=amd64
PLATFORM=$(uname -s)_$ARCH
curl -sLO "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$PLATFORM.tar.gz"

# Make a local bin
mkdir -p ./bin
tar -xzf eksctl_$PLATFORM.tar.gz -C ./bin && rm eksctl_$PLATFORM.tar.gz
```

Also make sure you have awscli installed (`pip install awscli`). If you forget to do this,
 you won't have your `kubectl` working off the bat and you'll need to install it and run:
 
```bash
$ aws eks --region us-east-1 update-kubeconfig --name scaling-study-efa
```

## Usage

The following can be run for each of the vanilla ([hpc6a.16xlarge](https://aws.amazon.com/ec2/instance-types/hpc6/)) and [hpc7g.16xlarge])()
clusters. Note that we can't match them 1:1 for instance sizes, but we can match for cores
(which I think is important for LAMMPS?) E.g., a size 8 cluster for the hpc6a is matched to a size 12
cluster for hpc7g. Here are specs for both:

| Name         | Cores | Memory (GiB) | Network Bandwidth (Gbps) | Cluster Size | Total Cores |
|--------------|-------|--------------|--------------------------|--------------|-------------|
|hpc6a.48xlarge| 96    | 384          | 25                       | 8            | 768 (8*96)  |
|hpc7g.16xlarge| 64    | 128          | Up to 200                | 12           | 768 (12*64) |

I got this information from [this table](https://aws.amazon.com/ec2/instance-types/#HPC_Optimized).
The memory unfortunately is not comparable, but (I hope) that's OK. If it's not, we will likely
not be able to easily compare the two.

### hpc6a.48xlarge

Here is how to create the initial "vanilla" cluster (without the cool new nodes!)

```bash
$ ./bin/eksctl create cluster -f ./config/eks-efa-vanilla-cluster-config.yaml
```

<details>

<summary>Cluster creation details</summary>

```console
2023-06-25 16:40:01 [ℹ]  eksctl version 0.146.0
2023-06-25 16:40:01 [ℹ]  using region us-east-2
2023-06-25 16:40:01 [ℹ]  subnets for us-east-2b - public:192.168.0.0/19 private:192.168.64.0/19
2023-06-25 16:40:01 [ℹ]  subnets for us-east-2c - public:192.168.32.0/19 private:192.168.96.0/19
2023-06-25 16:40:01 [ℹ]  nodegroup "workers" will use "" [AmazonLinux2/1.27]
2023-06-25 16:40:01 [ℹ]  using SSH public key "/home/vanessa/.ssh/id_eks.pub" as "eksctl-scaling-study-efa-nodegroup-workers-4e:93:d9:47:eb:81:3e:4f:1b:e0:44:ac:af:c6:ac:b3" 
2023-06-25 16:40:02 [ℹ]  using Kubernetes version 1.27
2023-06-25 16:40:02 [ℹ]  creating EKS cluster "scaling-study-efa" in "us-east-2" region with managed nodes
2023-06-25 16:40:02 [ℹ]  1 nodegroup (workers) was included (based on the include/exclude rules)
2023-06-25 16:40:02 [ℹ]  will create a CloudFormation stack for cluster itself and 0 nodegroup stack(s)
2023-06-25 16:40:02 [ℹ]  will create a CloudFormation stack for cluster itself and 1 managed nodegroup stack(s)
2023-06-25 16:40:02 [ℹ]  if you encounter any issues, check CloudFormation console or try 'eksctl utils describe-stacks --region=us-east-2 --cluster=scaling-study-efa'
2023-06-25 16:40:02 [ℹ]  Kubernetes API endpoint access will use default of {publicAccess=true, privateAccess=false} for cluster "scaling-study-efa" in "us-east-2"
2023-06-25 16:40:02 [ℹ]  CloudWatch logging will not be enabled for cluster "scaling-study-efa" in "us-east-2"
2023-06-25 16:40:02 [ℹ]  you can enable it with 'eksctl utils update-cluster-logging --enable-types={SPECIFY-YOUR-LOG-TYPES-HERE (e.g. all)} --region=us-east-2 --cluster=scaling-study-efa'
2023-06-25 16:40:02 [ℹ]  
2 sequential tasks: { create cluster control plane "scaling-study-efa", 
    2 sequential sub-tasks: { 
        wait for control plane to become ready,
        create managed nodegroup "workers",
    } 
}
2023-06-25 16:40:02 [ℹ]  building cluster stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:40:03 [ℹ]  deploying stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:40:33 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:41:03 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:42:04 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:43:04 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:44:04 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:45:05 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:46:05 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:47:05 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:48:05 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:49:06 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-06-25 16:51:08 [ℹ]  building managed nodegroup stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-06-25 16:51:09 [ℹ]  skipping us-east-2c from selection because it doesn't support the following instance type(s): hpc6a.48xlarge
2023-06-25 16:51:09 [ℹ]  EFA requires all nodes be in a single subnet, arbitrarily choosing one: [subnet-0bdae8c5d11f4dee3]
2023-06-25 16:51:09 [ℹ]  deploying stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-06-25 16:51:10 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-06-25 16:51:40 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-06-25 16:52:31 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-06-25 16:54:21 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-06-25 16:56:05 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-06-25 16:56:05 [ℹ]  waiting for the control plane to become ready
2023-06-25 16:56:05 [✔]  saved kubeconfig as "/home/vanessa/.kube/config"
2023-06-25 16:56:05 [ℹ]  1 task: { install EFA device plugin }
W0625 16:56:06.253876 1050387 warnings.go:70] spec.template.spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms[0].matchExpressions[0].key: beta.kubernetes.io/instance-type is deprecated since v1.17; use "node.kubernetes.io/instance-type" instead
W0625 16:56:06.253985 1050387 warnings.go:70] spec.template.metadata.annotations[scheduler.alpha.kubernetes.io/critical-pod]: non-functional in v1.16+; use the "priorityClassName" field instead
2023-06-25 16:56:06 [ℹ]  created "kube-system:DaemonSet.apps/aws-efa-k8s-device-plugin-daemonset"
2023-06-25 16:56:06 [ℹ]  as you have enabled EFA, the EFA device plugin was automatically installed.
2023-06-25 16:56:06 [✔]  all EKS cluster resources for "scaling-study-efa" have been created
2023-06-25 16:56:06 [ℹ]  nodegroup "workers" has 8 node(s)
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-12-232.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-13-139.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-13-214.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-16-162.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-21-44.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-27-35.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-31-106.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-5-125.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  waiting for at least 8 node(s) to become ready in "workers"
2023-06-25 16:56:06 [ℹ]  nodegroup "workers" has 8 node(s)
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-12-232.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-13-139.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-13-214.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-16-162.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-21-44.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-27-35.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-31-106.us-east-2.compute.internal" is ready
2023-06-25 16:56:06 [ℹ]  node "ip-192-168-5-125.us-east-2.compute.internal" is ready
2023-06-25 16:56:10 [ℹ]  kubectl command should work with "/home/vanessa/.kube/config", try 'kubectl get nodes'
2023-06-25 16:56:10 [✔]  EKS cluster "scaling-study-efa" in "us-east-2" region is ready

```

</details>

Note this takes 15-20 minutes. When it's done, note that they [still haven't fixed the efa bug](https://github.com/weaveworks/eksctl/issues/6222#issuecomment-1606309482), 
and there are also deprecated fields (that likely led to more bugs) so we are going to get the manifest and fix it ourselves.

```bash
$ kubectl delete -f ./config/efa-device-plugin.yaml
# I waited for the pods to go away and then:
$ kubectl apply -f ./config/efa-device-plugin.yaml
```

And install the flux operator:

```bash
$ kubectl apply -f ./config/flux-operator.yaml
```

This will create our size 12 cluster that we will be running LAMMPS on many times:

```bash
$ kubectl create namespace flux-operator
$ kubectl apply -f minicluster-12.yaml
```

You'll want to wait until your pods are ready, and then save some metadata about both pods and nodes:

```bash
$ mkdir -p ./data
$ kubectl get nodes -o json > data/hpc7g-nodes.json
$ kubectl get -n flux-operator pods -o json > data/hpc7g-pods.json
```

And copy your run-experiments script into the laed broker pod:

```bash
POD=$(kubectl get pods -n flux-operator -o json | jq -r .items[0].metadata.name)

# This will copy configs / create directories for it
kubectl cp -n flux-operator ./scripts/run-experiments.py ${POD}:/home/flux/examples/reaxff/HNS/run-experiments.py -c flux-sample
```

and then shell in:

```bash
$ kubectl exec -it -n flux-operator ${POD} bash
```
You should be in the experiment directory:

```bash
cd /opt/lammps/examples/reaxff/HNS
```

Connect to the main broker:

```bash
. /etc/profile.d/z10_spack_environment.sh 
cd /opt/spack-environment
. /opt/spack-environment/spack/share/spack/setup-env.sh
spack env activate .
cd /home/flux/examples/reaxff/HNS
sudo -u flux -E PYTHONPATH=$PYTHONPATH -E PATH=$PATH -E HOME=/home/flux -E FI_EFA_USE_DEVICE_RDMA=1 -E RDMAV_FORK_SAFE=1 flux proxy local:///run/flux/local bash
```

Let's write output to our home. This might be wonky because we don't have a shared filesystem.
Note that since this container has an old version of Flux (it needs a rebuild for a more proper experiment)
the run-experiments script does a `flux mini submit` instead of  `flux submit`. When we update
the versions of Flux in the container this will need to be updated. Then, here is a test run:

```bash
$ python3 ./run-experiments.py --outdir /home/flux/test-size-1 \
          --workdir /home/flux/examples/reaxff/HNS \
          --times 2 -N 8 --tasks 768 lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
```

And the actual run (20x)

```bash
$ python3 ./run-experiments.py --outdir /home/flux/size-64-16-16 \
          --workdir /opt/lammps/examples/reaxff/HNS \
          --times 20 -N 8 --tasks 768 lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -nocite
```

An example command looks like this:

```bash
flux mini submit -N 8 -n 768 --output /home/flux/size-64-16-16/lammps-18.log --error /home/flux/size-64-16-16/lammps-18.log -ompi=openmpi@5 -c 1 -o cpu-affinity=per-task --watch -vvv lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -nocite
```
```console
ƒMD9tnvnb: 0.000s submit
ƒMD9tnvnb: 0.012s validate
ƒMD9tnvnb: 0.023s depend
ƒMD9tnvnb: 0.023s priority
ƒMD9tnvnb: 0.057s alloc
ƒMD9tnvnb: 0.061s start
ƒMD9tnvnb: 0.058s exec.init
ƒMD9tnvnb: 0.059s exec.starting
ƒMD9tnvnb: 0.133s exec.shell.init
ƒMD9tnvnb: 97.800s finish
ƒMD9tnvnb: complete: status=0
ƒMD9tnvnb: 97.802s release
ƒMD9tnvnb: 97.802s free
ƒMD9tnvnb: 97.803s clean
```

We are saving output by sizes, etc. When it's done running, you can copy the entire output directory
from the pod to your local machine:

```bash
POD=$(kubectl get pods -n flux-operator -o json | jq -r .items[0].metadata.name)
mkdir -p ./data/hpc6a
kubectl cp -n flux-operator ${POD}:/home/flux/test-size-1 ./data/hpc6a/test-size-1 -c flux-sample
kubectl cp -n flux-operator ${POD}:/home/flux/size-64-16-16 ./data/hpc6a/size-64-16-16 -c flux-sample
```

In the future we will make our lives easier and put these under a common root that is not home!

#### Clean Up

Delete the cluster with eksctl

```bash
$ eksctl delete cluster -f ./config/eks-efa-vanilla-cluster-config.yaml 
```

### hpc7g.16xlarge

Here is how to create the hpc7g.16xlarge cluster:

```bash
$ ./bin/eksctl create cluster -f ./config/eks-efa-hpc7g-cluster-config.yaml
```

Note that the number of nodes, and zones are different, and I tried [this](https://eksctl.io/announcements/nodegroup-override-announcement/)
to use a custom AMI. It did not work, so I made a [custom branch](https://github.com/weaveworks/eksctl/compare/main...researchapps:eksctl:add/hpc7g-node-arm-support?expand=1) 
to add support for the new instance type. Note that in my two effors, the plugin could not find any devices. This likely needs further debugging.

```bash
$ kubectl logs -n kube-system  aws-efa-k8s-device-plugin-daemonset-5jpqc
2023/06/26 04:35:54 Fetching EFA devices.
2023/06/26 04:35:54 No devices found.
```

We still need to get around the efa bug.  I find it works better to completely delete
and re-apply.

```bash
$ kubectl delete -f ./config/efa-device-plugin.yaml
$ kubectl apply -f ./config/efa-device-plugin.yaml
```

Here are cluster creation details:

<details>

<summary>Cluster creation details</summary>

```console
```

</details>

We don't have EFA, but I'm going to continue anyway to test the ARM image and get a baseline.
It was here that I realized we also needed an arm build for the Flux Operator! So I threw one together:

```bash
$ kubectl apply -f ./config/flux-operator-arm.yaml
```

This will create our size 12 cluster that we will be running LAMMPS on many times:

```bash
$ kubectl create namespace flux-operator
$ kubectl apply -f minicluster-12.yaml
```

You'll want to wait until your pods are ready, and then save some metadata about both pods and nodes:

```bash
$ mkdir -p ./data
$ kubectl get nodes -o json > data/hpc7g-noefa-nodes.json
$ kubectl get -n flux-operator pods -o json > data/hpc7g-noefa-pods.json
```

Note that for this experiment, since the first time we didn't have working EFA, 
we ran without EFA. And copy your run-experiments script into the laed broker pod:

```bash
POD=$(kubectl get pods -n flux-operator -o json | jq -r .items[0].metadata.name)

# This will copy configs / create directories for it
kubectl cp -n flux-operator ./scripts/run-experiments.py ${POD}:/home/flux/examples/reaxff/HNS/run-experiments.py -c flux-sample
```

and then shell in:

```bash
$ kubectl exec -it -n flux-operator ${POD} bash
```
You should be in the experiment directory:

```bash
cd /opt/lammps/examples/reaxff/HNS
```

Connect to the main broker (after all the spack stuff):

```bash
. /etc/profile.d/z10_spack_environment.sh 
cd /opt/spack-environment
. /opt/spack-environment/spack/share/spack/setup-env.sh
spack env activate .
cd /home/flux/examples/reaxff/HNS
# With EFA
sudo -u flux -E PYTHONPATH=$PYTHONPATH -E PATH=$PATH -E HOME=/home/flux -E FI_EFA_USE_DEVICE_RDMA=1 -E RDMAV_FORK_SAFE=1 flux proxy local:///run/flux/local bash
# or without EFA
sudo -u flux -E PYTHONPATH=$PYTHONPATH -E PATH=$PATH -E HOME=/home/flux flux proxy local:///run/flux/local bash
```

Let's write output to our home. This might be wonky because we don't have a shared filesystem.
Note that since this container has an old version of Flux (it needs a rebuild for a more proper experiment)
we need to change `flux submit` to `flux mini submit`. Then, here is a test run:

```bash
mkdir -p /home/flux/data
$ python3 ./run-experiments.py --outdir /home/flux/data/test-size-1 \
          --workdir /home/flux/examples/reaxff/HNS \
          --times 2 -N 12 --tasks 768 lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
```

And the actual run (20x)

```bash
$ python3 ./run-experiments.py --outdir /home/flux/data/size-64-16-16 \
          --workdir /opt/lammps/examples/reaxff/HNS \
          --times 20 -N 12 --tasks 768 lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -nocite
```

When it's done running, you can copy the entire output directory from the pod to your local machine:

```bash
POD=$(kubectl get pods -n flux-operator -o json | jq -r .items[0].metadata.name)
kubectl cp -n flux-operator ${POD}:/home/flux/data ./data/hpc7g-noefa -c flux-sample
```

### Clean Up

Delete the cluster with eksctl

```bash
$ eksctl delete cluster -f ./config/eks-efa-hpc7g-cluster-config.yaml 
```

## Analysis

**TBA** not sure it's worth it here.
