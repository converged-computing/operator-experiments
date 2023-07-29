# Testing HPC7G with A Larger Problem Size

This log will include complete documentation that is being requested by AWS for debugging EFA.
To read our initial debugging, see [DEBUGGING](DEBUGGING.md). We sent the logs to the agent
and he determined that the filesystem was too small to download dependencies for the device.
So for this fix I am going to try increasing the size of the [node root volume](https://eksctl.io/introduction/?h=volume#volume-size).
A summary of debugging is below, followed by a short experiment to see if increasing the disk resolves the error.

## Debugging

The AWS support did fantastic debugging! It looks like the log collector export allowed him to debug the initd (and similar startup) scripts, and the underlying issue here is that the node ran out of room to download the needed packages for EFA?

```console
Stderr: 
        
        Transaction check error:
          installing package openmpi40-aws-4.1.5-3.aarch64 needs 3MB on the / filesystem
          installing package efa-2.5.0-1.amzn2.aarch64 needs 3MB on the / filesystem
          installing package libfabric-aws-devel-1.18.1-1.amzn2.aarch64 needs 7MB on the / filesystem
          installing package efa-profile-1.5-1.amzn2.noarch needs 7MB on the / filesystem
          installing package efa-config-1.15-1.amzn2.noarch needs 7MB on the / filesystem
        
        Error Summary
        -------------
        Disk Requirements:
          At least 7MB more space needed on the / filesystem.
        
        Error: Failed to install packages.
        Error: failed to install EFA packages, exiting
        /var/lib/cloud/instances/i-081cafd3368ab4d44/boothooks/part-001: line 7: pop: command not found
        /usr/bin/cloud-init-per: line 63: /opt/amazon/efa/bin/fi_info: No such file or directory
```

He is saying that the worker nodes download to tmp, and there isn’t enough room:

> Further, I have checked the user data being used with worker nodes and found that it is installing packages in /tmp directory which might be falling short of 7 MB:

```console
--------
cloud-init-per once yum_wget yum install -y wget
cloud-init-per once wget_efa wget -q --timeout=20 https://s3-us-west-2.amazonaws.com/aws-efa-installer/aws-efa-installer-latest.tar.gz  -O /tmp/aws-efa-installer-latest.tar.gz

cloud-init-per once tar_efa tar -xf /tmp/aws-efa-installer-latest.tar.gz -C /tmp
pushd /tmp/aws-efa-installer
cloud-init-per once install_efa ./efa_installer.sh -y -g
pop /tmp/aws-efa-installer
--------
And he’s asking us to:

So, I request you to review the user data and try out the different directory(with sufficient space if possible) with userdata. Also, please run the command “df -h” in both nodes (working and broken) and compare the output. Moreover, if you need further guidance regarding this EC2 issue, please reach out to EC2 team for better insights (if required) as I am from EKS team and having limited visibility to EC2 resources. Also, if you have any query regarding EKS, please reply back, I will be more than happy to help you.
Although I’m not sure this is something we are explicitly doing? So I think we have a few options - figure out where this command is generated (and try to fix it), or figure out how to give more filesystem space to the worker node. I’m going to start looking at code soon to see if it’s something done by eksctl (that we can debug) and we might suspect that the change is that they reduced the default filesystem size (somewhere).
```

## eksctl create cluster

Note that "The default volume size is 80G." and we are minimally 7MB short, so I'm going to try bumping up to 150.
This was done by changing the eksctl config.

```console
$ ./bin/eksctl create cluster -f ./config/eks-config.yaml
```

Note this didn't hit the bug - we still somehow ran out of space. I suspect the filesystem we see during init is not the same as what we see after (where I'm able to shell in and easily run the installer with no space issues).
We will need to debug this further. In the meantime, I've manually installed EFA on all nodes and I'm going to run the larger problem size experiment. First, ensure all the daemon sets are running:

```console
NAME                                        READY   STATUS    RESTARTS         AGE   IP               NODE                             NOMINATED NODE   READINESS GATES
aws-efa-k8s-device-plugin-daemonset-2kdg8   1/1     Running   11 (5m15s ago)   31m   192.168.26.44    ip-192-168-26-44.ec2.internal    <none>           <none>
aws-efa-k8s-device-plugin-daemonset-4plrm   1/1     Running   0                31m   192.168.9.214    ip-192-168-9-214.ec2.internal    <none>           <none>
aws-efa-k8s-device-plugin-daemonset-6vwdx   1/1     Running   0                31m   192.168.12.64    ip-192-168-12-64.ec2.internal    <none>           <none>
aws-efa-k8s-device-plugin-daemonset-8688t   1/1     Running   7 (25m ago)      31m   192.168.19.145   ip-192-168-19-145.ec2.internal   <none>           <none>
aws-efa-k8s-device-plugin-daemonset-9kgmz   1/1     Running   11 (5m7s ago)    31m   192.168.11.152   ip-192-168-11-152.ec2.internal   <none>           <none>
aws-efa-k8s-device-plugin-daemonset-njwrr   1/1     Running   10 (10m ago)     31m   192.168.21.18    ip-192-168-21-18.ec2.internal    <none>           <none>
aws-efa-k8s-device-plugin-daemonset-pchhg   1/1     Running   11 (5m24s ago)   31m   192.168.12.254   ip-192-168-12-254.ec2.internal   <none>           <none>
aws-efa-k8s-device-plugin-daemonset-x277w   1/1     Running   11 (5m28s ago)   31m   192.168.15.189   ip-192-168-15-189.ec2.internal   <none>           <none>
aws-node-5rzmq                              1/1     Running   0                33m   192.168.19.145   ip-192-168-19-145.ec2.internal   <none>           <none>
```

### Install Flux Operator

Now let's install an arm version of the Flux Operator.

```bash
$ kubectl apply -f ./config/flux-operator-arm.yaml
```

This will create our size 12 cluster that we will be running LAMMPS on many times:

```bash
$ kubectl create namespace flux-operator
$ kubectl apply -f ./config/minicluster-efa.yaml # 18.1.1
```

This will take a few minutes to pull the large container and start flux.

### Save Metadata 

In the meantime, save data about the nodes.

```bash
$ mkdir -p ./data
$ kubectl get nodes -o json > data/nodes.json
```

Ensure the pods are running. Note that the workers have a 60 second sleep, so you'll need to wait until you see the quroum is full in index 0:

```bash
kubectl logs -n flux-operator flux-sample-0-bkmm8 
```
```console
broker.err[0]: quorum delayed: waiting for flux-sample-3 (rank 3)
broker.info[0]: online: flux-sample-[0-7] (ranks 0-7)
broker.err[0]: quorum reached
broker.info[0]: quorum-full: quorum->run 1.00568m
```

We could probably reduce that sleep or just remove it, but I was being conservative.

### Run Experiments

Then copy your run-experiments script into the lead broker pod:

```bash
POD=$(kubectl get pods -n flux-operator -o json | jq -r .items[0].metadata.name)

# This will copy configs / create directories for it
kubectl cp -n flux-operator ./scripts/run-experiments.py ${POD}:/home/flux/examples/reaxff/HNS/run-experiments.py -c flux-sample
```

and then shell in:

```bash
$ kubectl exec -it -n flux-operator ${POD} bash
```
You should be in the experiment directory.
Connect to the main broker (after all the spack stuff):

```bash
. /etc/profile.d/z10_spack_environment.sh 
cd /opt/spack-environment
. /opt/spack-environment/spack/share/spack/setup-env.sh
spack env activate .
cd /home/flux/examples/reaxff/HNS
# With EFA
sudo -u flux -E PYTHONPATH=$PYTHONPATH -E PATH=$PATH -E HOME=/home/flux -E FI_PROVIDER=efa -E OMPI_MCA_btl=self,ofi -E RDMAV_FORK_SAFE=1 -E FI_EFA_USE_DEVICE_RDMA=1 flux proxy local:///run/flux/local bash
```

Sanity check we have our resources (sometimes they might not be all ready right away, so wait)

```
 flux resource list
     STATE NNODES   NCORES    NGPUS NODELIST
      free      8      512        0 flux-sample-[0-7]
 allocated      0        0        0 
      down      0        0        0 
```

Let's write output to our home. This might be wonky because we don't have a shared filesystem.
Sanity check these variables are in the environment, and also test doing a `flux run env | grep <NAME>` to 
verify they will show up for a flux run.

```bash
# restricts to only efa as OFI option
export FI_PROVIDER=efa
export OMPI_MCA_btl=self,ofi
export RDMAV_FORK_SAFE=1
export FI_EFA_USE_DEVICE_RDMA=1
```

Double check that efa is there.

```bash
$ fi_info -p efa
```
```console
provider: efa
    fabric: efa
    domain: rdmap0s6-rdm
    version: 118.10
    type: FI_EP_RDM
    protocol: FI_PROTO_EFA
provider: efa
    fabric: efa
    domain: rdmap0s6-dgrm
    version: 118.10
    type: FI_EP_DGRAM
    protocol: FI_PROTO_EFA
```

What are the two components? Let's prepare a small test run. This will use flux submit,
and given that carries forward the current environment, it should work to use EFA (I think).

```bash
mkdir -p /home/flux/data
python3 ./run-experiments.py --outdir /home/flux/data/test-size-1 \
          --workdir /home/flux/examples/reaxff/HNS \
          --times 2 -N 8 --tasks 512 lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
```

Then let's time one run with a large problem size to estimate what it will take.
Note that the even larger size (128 x 32 x 32) did not work.

```bash
python3 ./run-experiments.py --outdir /home/flux/data/size-64-32-32-efa \
        --workdir /opt/lammps/examples/reaxff/HNS \
        --times 3 -N 8 --tasks 512 lmp -v x 64 -v y 32 -v z 32 -in in.reaxc.hns -nocite
```

This took about 6 minutes, so I'm only going to run it 3 times.

```bash
$ python3 ./run-experiments.py --outdir /home/flux/data/size-64-16-16-efa \
          --workdir /opt/lammps/examples/reaxff/HNS \
          --times 3 -N 8 --tasks 512 lmp -v x 64 -v y 32 -v z 32 -in in.reaxc.hns -nocite
```

When you are done, copy the data from the instance:

```bash
POD=$(kubectl get pods -n flux-operator -o json | jq -r .items[0].metadata.name)
kubectl cp -n flux-operator ${POD}:/home/flux/data ./data/hpc7g-efa -c flux-sample
```

Save pod metadata:

```bash
$ kubectl get -n flux-operator pods -o json > data/pods-efa.json
```

### Testing without EFA

Let's delete the first MiniCluster and EFA:

```bash
kubectl delete -f config/minicluster-efa.yaml
kubectl delete daemonset -n kube-system aws-efa-k8s-device-plugin-daemonset
```

When you've confirmed the efa pods and previous flux-sample pods are gone, create the new MiniCluster:

```bash
kubectl create -f config/minicluster-no-efa.yaml
```

That will again take a minute. When they are running:

```bash
$ kubectl get -n flux-operator pods -o json > data/pods-no-efa.json
```

Now we are going to do the same thing we did before, but without EFA.
And let's repeat all of the above!


```bash
POD=$(kubectl get pods -n flux-operator -o json | jq -r .items[0].metadata.name)

# This will copy configs / create directories for it
kubectl cp -n flux-operator ./scripts/run-experiments.py ${POD}:/home/flux/examples/reaxff/HNS/run-experiments.py -c flux-sample
```

and then shell in:

```bash
$ kubectl exec -it -n flux-operator ${POD} bash
```
You should be in the experiment directory.
Connect to the main broker (after all the spack stuff):

```bash
. /etc/profile.d/z10_spack_environment.sh 
cd /opt/spack-environment
. /opt/spack-environment/spack/share/spack/setup-env.sh
spack env activate .
cd /home/flux/examples/reaxff/HNS
# Without EFA
sudo -u flux -E PYTHONPATH=$PYTHONPATH -E PATH=$PATH -E HOME=/home/flux flux proxy local:///run/flux/local bash
```

This should now fail.

```bash
$ fi_info -p efa
```
```console
fi_getinfo: -61
```

Sanity check we have our resources (sometimes they might not be all ready right away, so wait)

```
 flux resource list
     STATE NNODES   NCORES    NGPUS NODELIST
      free      8      512        0 flux-sample-[0-7]
 allocated      0        0        0 
      down      0        0        0 
```

Let's prepare a small test run. This will use flux submit.

```bash
mkdir -p /home/flux/data
python3 ./run-experiments.py --outdir /home/flux/data/test-size-1 \
          --workdir /home/flux/examples/reaxff/HNS \
          --times 2 -N 8 --tasks 512 lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
```

Let's test the same problem size.

```bash
python3 ./run-experiments.py --outdir /home/flux/data/size-64-32-32-efa \
        --workdir /opt/lammps/examples/reaxff/HNS \
        --times 3 -N 8 --tasks 512 lmp -v x 64 -v y 32 -v z 32 -in in.reaxc.hns -nocite
```

When you are done, copy the data from the instance:

```bash
POD=$(kubectl get pods -n flux-operator -o json | jq -r .items[0].metadata.name)
kubectl cp -n flux-operator ${POD}:/home/flux/data ./data/hpc7g-no-efa -c flux-sample
```

### Clean Up

Delete the cluster with eksctl

```bash
$ eksctl delete cluster -f ./config/eks-config.yaml 
```

## Results

I did 3 runs (with and without efa) and for LAMMPS, they are trivially different
```console
hpc7g-no-efa/size-64-32-32-efa/lammps-0.log:Total wall time: 0:06:17
hpc7g-no-efa/size-64-32-32-efa/lammps-1.log:Total wall time: 0:06:18
hpc7g-no-efa/size-64-32-32-efa/lammps-2.log:Total wall time: 0:06:18
   hpc7g-efa/size-64-32-32-efa/lammps-0.log:Total wall time: 0:06:17
   hpc7g-efa/size-64-32-32-efa/lammps-1.log:Total wall time: 0:06:17
   hpc7g-efa/size-64-32-32-efa/lammps-2.log:Total wall time: 0:06:17
```

The runtime reported by flux is very similar

```console
hpc7g-no-efa/size-64-32-32-efa/lammps-1-info.json:    "runtime": 380.6488137245178,
hpc7g-no-efa/size-64-32-32-efa/lammps-0-info.json:    "runtime": 380.382937669754,
hpc7g-no-efa/size-64-32-32-efa/lammps-2-info.json:    "runtime": 380.6019821166992,
   hpc7g-efa/size-64-32-32-efa/lammps-1-info.json:    "runtime": 380.2909417152405,
   hpc7g-efa/size-64-32-32-efa/lammps-0-info.json:    "runtime": 380.9786250591278,
   hpc7g-efa/size-64-32-32-efa/lammps-2-info.json:    "runtime": 380.92184114456177,
```

It's only 3 runs each, which isn't enough, and likely not significant, but at least I'd expect the two 6:18 times to have the slowest flux runtime (they do not).
Will go back to debugging / testing solutions for the filesystem, because that's the real issue. I was just curious to try the larger problem size (did not work, but maybe with more nodes it will?) and then sanity check run this size again.
