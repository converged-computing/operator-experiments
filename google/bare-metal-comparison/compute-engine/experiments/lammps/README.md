# Flux Framework LAMMPS Cluster Deployment

This deployment illustrates deploying a flux-framework cluster on Google Cloud
to run LAMMPS. All components are included here.

# Usage

Copy the variables to make your own variant:

```bash
$ cp lammps.tfvars.example lammps.tfvars
```

Make note that the machine types should match those you prepared in [build-images](../../build-images)
Initialize the deployment with the command:

```bash
$ terraform init
```

Since LAMMPS does not need a shared file system, we won't be mounting any buckets.

## Deploy

Then, deploy the cluster with the command:

```bash
$ terraform apply -var-file lammps.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=foundation-net \
  -var zone=us-central1-a
```

This will setup networking and all the instances! Note that
you can change any of the `-var` values to be appropriate for your environment.
Verify that the cluster is up:

```bash
$ gcloud compute ssh gffw-login-001 --zone us-central1-a
```

## Run Test Experiments

The easiest thing to do is to copy the file to run experiments to your home directory!

```bash
$ gcloud compute scp --zone us-central1-a ./run-experiments.py gffw-login-001:/home/sochat1_llnl_gov/run-experiments.py
```

And then shell in (as we did above)


```bash
$ gcloud compute ssh gffw-login-001 --zone us-central1-a
```

Go to the experiment directory with our files of interest

```bash
cd /opt/lammps/examples/reaxff/HNS
```

Try running the lammps experiment, given that lammps is installed on the nodes, and (for this example) we have two nodes only.
Note that by default, output data will be written to the present working directory in a "data" subfolder. Since
we don't have write in the experiment files folder, we direct to our home directory (it will be created):

```bash
$ python3 $HOME/run-experiments.py --outdir /home/sochat1_llnl_gov/data \
          --workdir /opt/lammps/examples/reaxff/HNS \
          --times 10 -N 2 --tasks 2 lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
```

<details>

<summary>Example Output</summary>

```console
         N: 2
     times: 10
     sleep: 10
    outdir: /home/sochat1_llnl_gov/data
     tasks: 2
   command: lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
   workdir: /opt/lammps/examples/reaxff/HNS
   dry-run: False
identifier: lammps
Submit ƒ31XLJ9fgb: 1 of 10
Submit ƒ31XQvVRh1: 2 of 10
Submit ƒ31XVVsD8j: 3 of 10
Submit ƒ31Xa6iyro: 4 of 10
Submit ƒ31Xehakas: 5 of 10
Submit ƒ31XjKvWbH: 6 of 10
Submit ƒ31XovnHKM: 7 of 10
Submit ƒ31XtXe43R: 8 of 10
Submit ƒ31XyCwncX: 9 of 10
Submit ƒ31Y439Ssh: 10 of 10

⭐️ Waiting for jobs to finish...
    Still waiting on job ƒ31XLJ9fgb, has state RUN
No longer waiting on job ƒ31XLJ9fgb, FINISHED 0!
    Still waiting on job ƒ31XQvVRh1, has state RUN
No longer waiting on job ƒ31XQvVRh1, FINISHED 0!
    Still waiting on job ƒ31XVVsD8j, has state RUN
No longer waiting on job ƒ31XVVsD8j, FINISHED 0!
    Still waiting on job ƒ31Xa6iyro, has state RUN
No longer waiting on job ƒ31Xa6iyro, FINISHED 0!
    Still waiting on job ƒ31Xehakas, has state RUN
No longer waiting on job ƒ31Xehakas, FINISHED 0!
    Still waiting on job ƒ31XjKvWbH, has state RUN
No longer waiting on job ƒ31XjKvWbH, FINISHED 0!
    Still waiting on job ƒ31XovnHKM, has state RUN
No longer waiting on job ƒ31XovnHKM, FINISHED 0!
    Still waiting on job ƒ31XtXe43R, has state RUN
No longer waiting on job ƒ31XtXe43R, FINISHED 0!
    Still waiting on job ƒ31XyCwncX, has state RUN
No longer waiting on job ƒ31XyCwncX, FINISHED 0!
    Still waiting on job ƒ31Y439Ssh, has state RUN
No longer waiting on job ƒ31Y439Ssh, FINISHED 0!
Jobs are complete, goodbye! 👋️
```

</details>

The script will hang after the last run waiting for the jobs to finish.
And that's it! The output directory in your home will have both log files (from the job output and error)
and the job info (json) from Flux:

```bash
$ ls /home/sochat1_llnl_gov/data/
```
```console
lammps-0-info.json  lammps-2-info.json  lammps-4-info.json  lammps-6-info.json  lammps-8-info.json
lammps-0.log        lammps-2.log        lammps-4.log        lammps-6.log        lammps-8.log
lammps-1-info.json  lammps-3-info.json  lammps-5-info.json  lammps-7-info.json  lammps-9-info.json
lammps-1.log        lammps-3.log        lammps-5.log        lammps-7.log        lammps-9.log
```

When you exit from the node, you can copy this to your computer to save.

```bash
$ mkdir -p ./data
$ gcloud compute scp --zone us-central1-a gffw-login-001:/home/sochat1_llnl_gov/data/* ./data
```

And that's really it :) When you are finished destroy the cluster:


```bash
$ terraform destroy -var-file lammps.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=foundation-net \
  -var zone=us-central1-a
```

## Run Experiments

These are the production experiments we are planning to run on a size 128 cluster, c2-highmem-112 instances:

| name | vCPU | cores | memory GB |
|------|------|-------|------------|
|c2d-standard-112 | 112 | 56 | 	448 |

For just LAMMPS, if LAMMPS takes 3 hours (for both the operator and compute engine) we estimate the cost to be 1,952.52.
This means if each setup takes 3 hours (for a total of 6) we will still be within our funding limit. We will start with these
experiments, get a sense of the time and cost, and then determine if we can run more experiments.

### Setup Compute Engine

The compute engine setup must be run separately from the Flux Operator setup.
For both, we will time creation, and run experiments in the same way - running 
jobs interactively. We will be using `lammps-production.tfvars` Note that this assumes
1 manager node + 1 login node + 126 compute nodes for a total of 128.
Then:

```bash
# Initiate the deployment
$ terraform init

# Deploy the cluster
$ time terraform apply -var-file lammps-production.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=foundation-net \
  -var zone=us-central1-a
```

Note that we are timing it, as a value to compare with creating the "same" cluster size in the Flux Operator.
We will then be interacting with the cluster from the login node.

```bash
# Copy the experiment running file over
$ gcloud compute scp --zone us-central1-a ./run-experiments.py gffw-login-001:/home/sochat1_llnl_gov/run-experiments.py

# Shell in!
$ gcloud compute ssh gffw-login-001 --zone us-central1-a
```

This run-experiments.py will run a set of experiments on each set of instance sizes, including 8,16,32,64, and 128.
Proceed to the [run lammps](#run-lammps) section for how to run the experiments using allocations.

### Setup Flux Operator

You will need to create the Kubernetes cluster:

```bash
$ time gcloud container clusters create flux-operator --cluster-dns=clouddns --cluster-dns-scope=cluster \
   --threads-per-core=1 \
   --region=us-central1-a --project $GOOGLE_PROJECT \
   --machine-type c2d-standard-112 --num-nodes=128 --enable-network-policy \
   --tags=flux-cluster --enable-intra-node-visibility

$ gcloud container clusters get-credentials flux-operator --zone us-central1-a --project $GOOGLE_PROJECT
$ kubectl create clusterrolebinding cluster-admin-binding --clusterrole cluster-admin --user $(gcloud config get-value core/account)
```

Record the times it takes to create. Then install the storage driver:

```bash
$ kubectl apply -k "github.com/ofek/csi-gcs/deploy/overlays/stable?ref=v0.9.0"
$ kubectl get CSIDriver,daemonsets,pods -n kube-system | grep csi
$ kubectl logs -l app=csi-gcs -c csi-gcs -n kube-system
$ kubectl apply -f operator/storageclass.yaml
```

Then install the operator.

```bash
$ kubectl create namespace flux-operator
$ kubectl apply -f operator/flux-operator.yaml
```

Then create the cluster - we are also creating one size 128 cluster, and will
create smaller allocations on it. You'll want to shell in to the broker:

```bash
$ kubectl exec -it -n flux-operator flux-sample-0-xxxx -- bash

# Flux should be running as root, so no need to run this as a user
$ flux proxy local:///run/flux/local bash
```

Proceed to the [run lammps](#run-lammps) section for how to run the experiments using allocations.

### Run LAMMPS 

Here are the commands to do for each one - they must be run one at a time.
Go to the experiment directory with our files of interest

```bash
cd /opt/lammps/examples/reaxff/HNS
```

Note that for each of the Python commands below, it will submit jobs that look like:

```bash
flux submit -N ${nodes} -n 448 --output ... --error lmp...
```

And the output directories differ for Compute Engine vs. the operator. 

```
# compute engine
export outdir=/home/sochat1_llnl_gov

# flux operator
export outdir=/workflow
```

And if they are running under an allocation of that many nodes, each job should use all of them.

#### Size 8

> IMPORTANT: we are first going to try a problem size of `-v x 64 -v y 32 -v z 16` for a size 8 setup, and if it takes longer than 3 minutes, we will cut and reduce to the original `-v x 64 -v y 16 -v z 16` 

Size 8 tasks should be 56 * 8 == 448?


```bash
flux alloc -N 8 /bin/bash
nodes=8
mkdir -p ${outdir}/data/size_${nodes}
cd /opt/lammps/examples/reaxff/HNS
python run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 448 --times 20 -N ${nodes} lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes} --identifier lammps-${nodes}
exit
```

#### Size 16

Size 16 tasks should be 56 * 16 == 896

```bash
flux alloc -N 16 /bin/bash
nodes=16
mkdir -p ${outdir}/data/size_${nodes}
cd /opt/lammps/examples/reaxff/HNS
python run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 896 --times 20 -N ${nodes} lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -
nocite --outdir $outdir/data/size_${nodes} --identifier lammps-${nodes}
exit
```


#### Size 32

Size 32 tasks should be 56 * 32 == 1792

```bash
flux alloc -N 32 /bin/bash
nodes=32
mkdir -p ${outdir}/data/size_${nodes}
cd /opt/lammps/examples/reaxff/HNS
python run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 1792 --times 20 -N ${nodes} lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes} --identifier lammps-${nodes}
exit
```

#### Size 64

Size 64 tasks should be 56 * 64 == 3584

```bash
flux alloc -N 64 /bin/bash
nodes=64
mkdir -p ${outdir}/data/size_${nodes}
cd /opt/lammps/examples/reaxff/HNS
python run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 3584 --times 20 -N ${nodes} lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes} --identifier lammps-${nodes}
exit
```

#### Size 128

Size 128 tasks should be 56 * 128 == 7168

```bash
flux alloc -N 128 /bin/bash
nodes=64
mkdir -p ${outdir}/data/size_${nodes}
cd /opt/lammps/examples/reaxff/HNS
python run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 7168 --times 20 -N ${nodes} lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes} --identifier lammps-${nodes}
exit
```

Note that the above works without thinking about storage because the terraform setup creates
a shared $HOME for us across nodes. For the Flux Operator we will need to bind a common storage bucket
instead.

### Finish Up

#### Compute Engine

When you exit from the login node, you need to copy all the output data to your computer:

```bash
$ mkdir -p ./data/compute-engine
$ gcloud compute scp --zone us-central1-a gffw-login-001:/home/sochat1_llnl_gov/data/* ./data/compute-engine
```

and then destroy the setup:

```bash
$ time terraform destroy -var-file lammps.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=foundation-net \
  -var zone=us-central1-a
```

Save the timing! And we will have a script to analyze (and compare to the operator)

#### Flux Operator

Exit from the broker and the node/pod, and then copy the results over with kubectl


```bash
$ mkdir -p /data/kubernetes
$ kubectl cp flux-operator/flux-sample-0-xxxx:/workflow ./data/kubernetes
```

And when you are sure you have all the data, cleanup the cluster:

```bash
$ gcloud container clusters delete --zone us-central1-a flux-operator
```
