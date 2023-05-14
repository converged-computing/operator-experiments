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
  -var network_name=flux-net \
  -var zone=us-central1-a
```

## Run Experiments

These are the production experiments we are planning to run on a size 128 cluster, c2-highmem-112 instances:

| name | vCPU | cores | memory GB | Notes |
|------|------|-------|------------|-----|
|c2d-standard-112 | 112 | 56 | 	448 | Didn't work well |
|c2-standard-60 | 60 | 30 | 240 | testing |

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
  -var network_name=flux-net \
  -var zone=us-central1-a
```

```console
# This was a size 128 cluster + manager
Apply complete! Resources: 141 added, 0 changed, 0 destroyed.

real    5m31.158s
user    0m22.369s
sys     0m1.684s

# This was a size 11 cluster + manager (I maxed out the compact placement for compute nodes)
Apply complete! Resources: 25 added, 0 changed, 0 destroyed.

real    2m14.245s
user    0m6.604s
sys     0m0.616s
```

Note that we are timing it, as a value to compare with creating the "same" cluster size in the Flux Operator.
We will then be interacting with the cluster from the login node.

```bash
# Copy the experiment running file over
$ gcloud compute scp --zone us-central1-a ./run-experiments.py gffw-login-001:/home/sochat1_llnl_gov/run-experiments.py

# Shell in!
$ gcloud compute ssh gffw-login-001 --zone us-central1-a
```
You'll need to wait until the other nodes are ready (e.g., they are likely installing lammps). You can watch the login
node doing the same with:

```bash
$ sudo journalctl -f
```

When the whole cluster is online:

```bash
 flux resource list
     STATE PROPERTIES NNODES   NCORES NODELIST
      free x86-64,c2d    128     7168 gffw-login-001,gffw-compute-a-[001-127]
 allocated                 0        0 
      down                 0        0 

     STATE PROPERTIES NNODES   NCORES NODELIST
      free x86-64,c2d     11      616 gffw-login-16-001,gffw-compute-a-16-[001-010]
 allocated                 0        0 
      down                 0        0 
```

This run-experiments.py will run a set of experiments on each set of instance sizes, including 8,16,32,64, and 128.
Proceed to the [run lammps](#run-lammps) section for how to run the experiments using allocations.

### Test Flux Operator

#### MiniKube

You might want to test the run before doing a larger one! I used minikube.

```bash
$ minikube start
$ minikube ssh docker pull ghcr.io/rse-ops/lammps-efa-rocky:tag-8
$ kubectl create namespace flux-operator
$ kubectl apply -f operator/flux-operator.yaml
$ kubectl apply -f operator/minicluster-minikube-test.yaml
```

You should see everything connect and work!

```bash
$ kubectl logs -n flux-operator flux-sample-0-xwvml -f 
```

<details>

<summary>Example output for MiniKube Test Run</summary>

```console
...
job-manager.info[0]: restart: 0 jobs
job-manager.info[0]: restart: 0 running jobs
job-manager.info[0]: restart: checkpoint.job-manager not found
broker.info[0]: rc1.0: running /opt/software/linux-rocky8-x86_64/gcc-8.5.0/flux-core-0.49.0-i5mwkh7xzw3ncjsw5droepelbamdlsf5/etc/flux/rc1.d/02-cron
broker.info[0]: rc1.0: running /opt/view/etc/flux/rc1.d/01-sched-fluxion
sched-fluxion-resource.info[0]: version 0.27.0
sched-fluxion-resource.warning[0]: create_reader: allowlist unsupported
sched-fluxion-resource.info[0]: populate_resource_db: loaded resources from core's resource.acquire
sched-fluxion-qmanager.info[0]: version 0.27.0
broker.info[0]: rc1.0: running /opt/view/etc/flux/rc1.d/02-cron
broker.info[0]: rc1.0: /opt/software/linux-rocky8-x86_64/gcc-8.5.0/flux-core-0.49.0-i5mwkh7xzw3ncjsw5droepelbamdlsf5/etc/flux/rc1 Exited (rc=0) 0.7s
broker.info[0]: rc1-success: init->quorum 0.717346s
broker.info[0]: online: flux-sample-0 (ranks 0)
broker.info[0]: online: flux-sample-[0-3] (ranks 0-3)
broker.info[0]: quorum-full: quorum->run 0.358625s
LAMMPS (29 Sep 2021 - Update 2)
OMP_NUM_THREADS environment is not set. Defaulting to 1 thread. (src/comm.cpp:98)
  using 1 OpenMP thread(s) per MPI task
Reading data file ...
  triclinic box = (0.0000000 0.0000000 0.0000000) to (22.326000 11.141200 13.778966) with tilt (0.0000000 -5.0260300 0.0000000)
  1 by 1 by 1 MPI processor grid
  reading atoms ...
  304 atoms
  reading velocities ...
  304 velocities
  read_data CPU = 0.002 seconds
Replicating atoms ...
  triclinic box = (0.0000000 0.0000000 0.0000000) to (44.652000 11.141200 13.778966) with tilt (0.0000000 -5.0260300 0.0000000)
  1 by 1 by 1 MPI processor grid
  bounding box image = (0 -1 -1) to (0 1 1)
  bounding box extra memory = 0.03 MB
  average # of replicas added to proc = 2.00 out of 2 (100.00%)
  608 atoms
  replicate CPU = 0.000 seconds
Neighbor list info ...
  update every 20 steps, delay 0 steps, check no
  max neighbors/atom: 2000, page size: 100000
  master list distance cutoff = 11
  ghost atom cutoff = 11
  binsize = 5.5, bins = 10 3 3
  2 neighbor lists, perpetual/occasional/extra = 2 0 0
  (1) pair reax/c, perpetual
      attributes: half, newton off, ghost
      pair build: half/bin/newtoff/ghost
      stencil: full/ghost/bin/3d
      bin: standard
  (2) fix qeq/reax, perpetual, copy from (1)
      attributes: half, newton off, ghost
      pair build: copy
      stencil: none
      bin: none
Setting up Verlet run ...
  Unit style    : real
  Current step  : 0
  Time step     : 0.1
Per MPI rank memory allocation (min/avg/max) = 114.6 | 114.6 | 114.6 Mbytes
Step Temp PotEng Press E_vdwl E_coul Volume 
       0          300   -113.27833    433.05108   -111.57687   -1.7014647    6854.7168 
      10    293.57213   -113.25935    1974.5403   -111.55823   -1.7011231    6854.7168 
      20    292.01532   -113.25425    4805.8939   -111.55347   -1.7007804    6854.7168 
      30    296.37471   -113.26711    7105.3152   -111.56678   -1.7003353    6854.7168 
      40    301.74636   -113.28288    11002.799   -111.58307   -1.6998056    6854.7168 
      50    301.84539   -113.28299    14627.007   -111.58366   -1.6993284    6854.7168 
      60    297.42965    -113.2701    12587.105    -111.5711   -1.6990006    6854.7168 
      70     293.0052   -113.25686    9334.5185    -111.5581     -1.69876    6854.7168 
      80    294.86535   -113.26233    10557.128   -111.56384   -1.6984896    6854.7168 
      90    302.52317   -113.28487    12424.959   -111.58667   -1.6982014    6854.7168 
     100    306.24646   -113.29619    13273.517   -111.59817   -1.6980134    6854.7168 
Loop time of 9.71341 on 1 procs for 100 steps with 608 atoms

Performance: 0.089 ns/day, 269.817 hours/ns, 10.295 timesteps/s
100.0% CPU use with 1 MPI tasks x 1 OpenMP threads

MPI task timing breakdown:
Section |  min time  |  avg time  |  max time  |%varavg| %total
---------------------------------------------------------------
Pair    | 8.0706     | 8.0706     | 8.0706     |   0.0 | 83.09
Neigh   | 0.1765     | 0.1765     | 0.1765     |   0.0 |  1.82
Comm    | 0.0033049  | 0.0033049  | 0.0033049  |   0.0 |  0.03
Output  | 0.00019419 | 0.00019419 | 0.00019419 |   0.0 |  0.00
Modify  | 1.4622     | 1.4622     | 1.4622     |   0.0 | 15.05
Other   |            | 0.0006713  |            |       |  0.01

Nlocal:        608.000 ave         608 max         608 min
Histogram: 1 0 0 0 0 0 0 0 0 0
Nghost:        6450.00 ave        6450 max        6450 min
Histogram: 1 0 0 0 0 0 0 0 0 0
Neighs:        240969.0 ave      240969 max      240969 min
Histogram: 1 0 0 0 0 0 0 0 0 0

Total # of neighbors = 240969
Ave neighs/atom = 396.33059
Neighbor list builds = 5
Dangerous builds not checked
Total wall time: 0:00:09
broker.info[0]: rc2.0: flux submit -n 1 --quiet -ompi=openmpi@5 -c 1 -o cpu-affinity=per-task --watch lmp -v x 2 -v y 1 -v z 1 -in in.reaxc.hns -nocite Exited (rc=0) 11.9s
broker.info[0]: rc2-success: run->cleanup 11.9078s
broker.info[0]: cleanup.0: flux queue stop --quiet --all --nocheckpoint Exited (rc=0) 0.1s
broker.info[0]: cleanup.1: flux cancel --user=all --quiet --states RUN Exited (rc=0) 0.1s
broker.info[0]: cleanup.2: flux queue idle --quiet Exited (rc=0) 0.1s
broker.info[0]: cleanup-success: cleanup->shutdown 0.370377s
broker.info[0]: online: flux-sample-[0-2] (ranks 0-2)
broker.info[0]: children-complete: shutdown->finalize 66.8552ms
broker.info[0]: rc3.0: running /opt/view/etc/flux/rc3.d/01-sched-fluxion
broker.info[0]: rc3.0: /opt/software/linux-rocky8-x86_64/gcc-8.5.0/flux-core-0.49.0-i5mwkh7xzw3ncjsw5droepelbamdlsf5/etc/flux/rc3 Exited (rc=0) 0.2s
broker.info[0]: rc3-success: finalize->goodbye 0.205441s
broker.info[0]: goodbye: goodbye->exit 0.038017ms
```

</details>

#### Google Cloud (small)

I was nervous about bringing up the full size cluster without testing first, so I did this for a test run.
Note that we are using Filestore for a consistent (separate) storage to try and mirror the NFS setup
on Compute Engine.

```bash
$ gcloud container clusters create flux-operator --cluster-dns=clouddns --cluster-dns-scope=cluster \
   --threads-per-core=1 \
   --addons=GcpFilestoreCsiDriver \
   --region=us-central1-a --project $GOOGLE_PROJECT \
   --machine-type c2d-standard-112 --num-nodes=4 --enable-network-policy \
   --tags=flux-cluster --enable-intra-node-visibility

$ gcloud container clusters get-credentials flux-operator --zone us-central1-a --project $GOOGLE_PROJECT
$ kubectl create clusterrolebinding cluster-admin-binding --clusterrole cluster-admin --user $(gcloud config get-value core/account)
```

Then install the operator.

```bash
$ kubectl create namespace flux-operator
$ kubectl apply -f operator/flux-operator.yaml
```

Create the persistent volume claim for filestore:

```bash
$ kubectl apply -f operator/pvc.yaml
```

And check on the status:

```bash
$ kubectl get -n flux-operator pvc
NAME   STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data   Pending                                      standard-rwx   6s
```

It will be pending under we make a request to use it! Let's do that by creating the MiniCluster:

```bash
$ kubectl apply -f operator/minicluster-test.yaml
```

You can use describe and get pods to see the status. Note that I saw some "NotTriggerScaleUp" issues
at first, and they sort of resolved themselves? I think likely Filestore wasn't ready yet.
When they are running, you'll want to copy the experiments file over

```bash
$ kubectl cp ./run-experiments.py flux-operator/flux-sample-0-xxx:/home/flux/run-experiments.py
```

...shell in and connect to the broker:

```bash
$ kubectl exec -it -n flux-operator flux-sample-0-xxxx -- bash
$ sudo -u flux -E HOME=/home/flux -E PATH=$PATH -E PYTHONPATH=$PYTHONPATH flux proxy local:///run/flux/local bash
```

And since we have flux installed under spack, we need a few special commands.

```bash
source /etc/profile.d/z10_spack_environment.sh
. /etc/profile.d/z10_spack_environment.sh 
cd /opt/spack-environment
. /opt/spack-environment/spack/share/spack/setup-env.sh
spack env activate .
cd /opt/lammps/examples/reaxff/HNS
```

Then proceed to the [run lammps](#run-lammps) section for how to run the experiments using allocations.


### Setup Flux Operator

Note that I tried this for each of size 64 and 128 on the c2d instance type, and  the networking didn't seem to take.
I disabled `--enable-network-policy` thinking that might be it, and adding a request for compact placement.
That didn't work either. So I fell back to the c2 family. This is how I created the Kubernetes cluster:

```bash
$ time gcloud container clusters create flux-operator --cluster-dns=clouddns --cluster-dns-scope=cluster \
   --threads-per-core=1 \
   --placement-type COMPACT \
   --addons=GcpFilestoreCsiDriver \
   --region=us-central1-a --project $GOOGLE_PROJECT \
   --machine-type c2d-standard-112 --num-nodes=8 \
   --tags=flux-cluster --enable-intra-node-visibility
#   --machine-type c2-standard-60 --num-nodes=64 \

$ gcloud container clusters get-credentials flux-operator --zone us-central1-a --project $GOOGLE_PROJECT
$ kubectl create clusterrolebinding cluster-admin-binding --clusterrole cluster-admin --user $(gcloud config get-value core/account)
```

Note for the above it only worked with 8 and smaller clusters! 

<details>

<summary>Relevant creation notes</summary>

```console
Default change: VPC-native is the default mode during cluster creation for versions greater than 1.21.0-gke.1500. To create advanced routes based clusters, please pass the `--no-enable-ip-alias` flag
Default change: During creation of nodepools or autoscaling configuration changes for cluster versions greater than 1.24.1-gke.800 a default location policy is applied. For Spot and PVM it defaults to ANY, and for all other VM kinds a BALANCED policy is used. To change the default values use the `--location-policy` flag.
Note: Your Pod address range (`--cluster-ipv4-cidr`) can accommodate at most 1008 node(s).
Creating cluster flux-operator in us-central1-a... Cluster is being health-checked (master is healthy)
```

Note that we've added Filestore. The time for size 128 (which didn't work):

```bash
NAME           LOCATION       MASTER_VERSION  MASTER_IP      MACHINE_TYPE      NODE_VERSION    NUM_NODES  STATUS
flux-operator  us-central1-a  1.25.8-gke.500  34.29.163.109  c2d-standard-112  1.25.8-gke.500  128        RUNNING

real    5m55.590s
user    0m4.339s
sys     0m0.302s
```

And for the 64:

```bash
NAME           LOCATION       MASTER_VERSION  MASTER_IP      MACHINE_TYPE      NODE_VERSION    NUM_NODES  STATUS
flux-operator  us-central1-a  1.25.8-gke.500  34.132.175.72  c2d-standard-112  1.25.8-gke.500  64         RUNNING

real    5m28.969s
user    0m3.927s
sys     0m0.210s
```

And 64 without network policy, and with compact placement:

```bash
NAME           LOCATION       MASTER_VERSION  MASTER_IP      MACHINE_TYPE      NODE_VERSION    NUM_NODES  STATUS
flux-operator  us-central1-a  1.25.8-gke.500  34.135.229.43  c2d-standard-112  1.25.8-gke.500  64         RUNNING

real    5m13.892s
user    0m3.804s
sys     0m0.206s
```

And with compact size 32

```bash
kubeconfig entry generated for flux-operator.
NAME           LOCATION       MASTER_VERSION  MASTER_IP       MACHINE_TYPE      NODE_VERSION    NUM_NODES  STATUS
flux-operator  us-central1-a  1.25.8-gke.500  34.121.131.102  c2d-standard-112  1.25.8-gke.500  32         RUNNING

real    5m39.386s
user    0m3.645s
sys     0m0.276s
```

And compact 16:

```bash
NAME           LOCATION       MASTER_VERSION  MASTER_IP       MACHINE_TYPE      NODE_VERSION    NUM_NODES  STATUS
flux-operator  us-central1-a  1.25.8-gke.500  34.171.243.186  c2d-standard-112  1.25.8-gke.500  16         RUNNING

real    5m9.406s
user    0m3.574s
sys     0m0.272s
```

And compact 8

```bash
NAME           LOCATION       MASTER_VERSION  MASTER_IP      MACHINE_TYPE      NODE_VERSION    NUM_NODES  STATUS
flux-operator  us-central1-a  1.25.8-gke.500  35.238.24.233  c2d-standard-112  1.25.8-gke.500  8          RUNNING

real    5m24.440s
user    0m3.915s
sys     0m0.166s
```

</details>


Then install the operator. Note this is a tagged test container that we are referring by hash to reproduce if needed later.

```bash
$ kubectl create namespace flux-operator
$ kubectl apply -f operator/flux-operator.yaml
```

Create the persistent volume claim for filestore:

```bash
$ kubectl apply -f operator/pvc.yaml
```

And check on the status:

```bash
$ kubectl get -n flux-operator pvc
NAME   STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data   Pending                                      standard-rwx   6s
```

It will be pending under we make a request to use it! Let's do that by creating the MiniCluster:
We are  creating one size 128 cluster, and will create smaller allocations on it. 

```bash
$ kubectl apply -f operator/minicluster-8.yaml
```

I found this confusing because at first they were all pending, and there was an error message about
insufficient cpu/memory. But then I waited - and they started to pop into "ContainerCreating" state
around 3 minutes, and then shortly after (when the container image was pulled) into "Running." 
I added a sleep of 1 minute to the worker pre command to ensure they started after the broker.

So wait until you see all the pods running, and verify that the flux-sample-0-xxx has a full quorum
by looking at the log for flux-sample-0-xxxx. You'll then want to copy the experiments file over

```bash
$ kubectl cp ./run-experiments.py flux-operator/flux-sample-0-xxx:/home/flux/run-experiments.py
```

...shell in and connect to the broker:

```bash
$ kubectl exec -it -n flux-operator flux-sample-0-xxxx -- bash
$ sudo -u flux -E HOME=/home/flux -E PATH=$PATH -E PYTHONPATH=$PYTHONPATH flux proxy local:///run/flux/local bash
```
And since we have flux installed under spack, we need a few special commands.

```bash
source /etc/profile.d/z10_spack_environment.sh
. /etc/profile.d/z10_spack_environment.sh 
cd /opt/spack-environment
. /opt/spack-environment/spack/share/spack/setup-env.sh
spack env activate .
cd /opt/lammps/examples/reaxff/HNS
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

And if they are running under an allocation of that many nodes, each job should use all of them. For the Flux operator, 
you'll want to copy the script to the shared space, as it won't be seen in flux home from any node aside from the broker.

```bash
sudo cp /home/flux/run-experiments.py /workflow/run-experiments.py
sudo chown flux /workflow/run-experiments.py
```

#### Size 2 Normal

> This was for testing only

Size 2 tasks should be 56 * 2 == 112

```bash
flux alloc -N 2 /bin/bash
nodes=2
# Note this was needed for the flux-operator, since it's not setup for home like traditional NFz
sudo mkdir -p ${outdir}/data/size_${nodes}
sudo chown ${USER} ${outdir}/data/size_${nodes}
cd /opt/lammps/examples/reaxff/HNS
python3 /workflow/run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 112 --times 20 -N ${nodes} lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes} --identifier lammps-${nodes}
exit
```

#### Size 2 Small

> This was for testing only

Size 2 tasks should be 56 * 2 == 112

```bash
flux alloc -N 2 /bin/bash
nodes=2
# Note this was needed for the flux-operator, since it's not setup for home like traditional NFS
sudo mkdir -p ${outdir}/data/size_${nodes}_small
sudo chown ${USER} ${outdir}/data/size_${nodes}_small
cd /opt/lammps/examples/reaxff/HNS
python3 /workflow/run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 112 --times 20 -N ${nodes} lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes}_small --identifier lammps-${nodes}
exit
```

#### Size 4

> This was for testing only

Size 4 tasks should be 56 * 4 == 224

```bash
flux alloc -N 4 /bin/bash
nodes=4
# Note this was needed for the flux-operator, since it's not setup for home like traditional NFS
sudo mkdir -p ${outdir}/data/size_${nodes}_small
sudo chown ${USER} ${outdir}/data/size_${nodes}_small
cd /opt/lammps/examples/reaxff/HNS
python3 /workflow/run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 224 --times 20 -N ${nodes} lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes}_small --identifier lammps-${nodes}
exit
```

Wow, this one seems to be running faster than the 8 node one? Why?!

#### Size 8

> IMPORTANT: we were first going to try a problem size of `-v x 64 -v y 32 -v z 16` for a size 8 setup, and if it takes longer than 3 minutes, we will cut and reduce to the original `-v x 64 -v y 16 -v z 16`. However on this size 8 cluster, even a 2 x 2 x 2 was taking a long time (and erroring) so I stuck to that.

Size 8 tasks should be 56 * 8 == 448?

```bash
flux alloc -N 8 /bin/bash
nodes=8
sudo mkdir -p ${outdir}/data/size_${nodes}_small
sudo chown ${USER} ${outdir}/data/size_${nodes}_small
cd /opt/lammps/examples/reaxff/HNS
python3 $HOME/run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 448 --times 20 -N ${nodes} lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes}_small --identifier lammps-${nodes}
exit
```
An example command:

```bash
flux submit -N 8 -n 448 --output /workflow//data/size_8_small/lammps-8-8.log --error /workflow//data/size_8_small/lammps-8-8.log -ompi=openmpi@5 -c 1 -o cpu-affinity=per-task --watch -vvv lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
```

#### Size 16

Size 16 tasks should be 56 * 16 == 896

```bash
flux alloc -N 16 /bin/bash
nodes=16
mkdir -p ${outdir}/data/size_${nodes}
cd /opt/lammps/examples/reaxff/HNS
python3 $HOME/run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 896 --times 20 -N ${nodes} lmp -v x 64 -v y 16 -v z 16 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes} --identifier lammps-${nodes}
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
nodes=128
mkdir -p ${outdir}/data/size_${nodes}
cd /opt/lammps/examples/reaxff/HNS
python3 $HOME/run-experiments.py --workdir /opt/lammps/examples/reaxff/HNS --tasks 7168 --times 20 -N ${nodes} lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite --outdir $outdir/data/size_${nodes} --identifier lammps-${nodes}
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
$ mkdir -p ./data/kubernetes-8
$ kubectl cp flux-operator/flux-sample-0-xxxx:/workflow/data ./data/kubernetes-8/
```


And when you are sure you have all the data, cleanup the cluster. You need to delete the pvc
explicitly, either here or in the console (it doesn't just cleanup with the cluster)!
Don't forget to save nodes and pods if you need to debug!

```bash
$ kubectl get pods -o json > ./data/kubernetes-8/pods.json
$ kubectl get nodes -o json > ./data/kubernetes-8/nodes.json
```

```bash
$ kubectl delete -f operator/pvc.yaml
$ gcloud container clusters delete --zone us-central1-a flux-operator
```

##### Debugging

Here is what the broker sees (that never connects to the workers). It's running with spack, hence the long PYTHONPATH

<details>

<summary>Broker Log</summary>

```console
Flux username: flux
flux user is already added.
flux user identifiers:
uid=1000(flux) gid=1000(flux) groups=1000(flux)

As Flux prefix for flux commands: sudo -u flux -E PYTHONPATH=/opt/view/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-pyrsistent-0.19.3-kbnsub7sugk32426tdippf4am733tcej/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-attrs-22.2.0-xxt3is4afn5dxqljxjw4c64grd5yrzl5/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-pycparser-2.21-uddpec2romvwc2poyrre7bj5qbp4jqwn/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-pyyaml-6.0-pdxwbzb2hyrgpx3bjkqizd77aoszdvbj/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-ply-3.11-k37gmnzkv6vavrjwznzws52zoswlirqa/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-jsonschema-4.17.3-audfdhc6xlie6ntzer4tpd7d6rle3eyp/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-cffi-1.15.1-4u7dbmm4ezxthpnafkculdrjlo7dewop/lib/python3.10/site-packages -E PATH=/opt/view/bin:/opt/spack-environment/spack/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin -E FI_EFA_USE_DEVICE_RDMA=1 -E RDMAV_FORK_SAFE=1

👋 Hello, I'm flux-sample-0
The main host is flux-sample-0
The working directory is /opt/lammps/examples/reaxff/HNS, contents include:
/opt/lammps/examples/reaxff/HNS:
README.txt      ffield.reax.hns  log.8Mar18.reaxc.hns.g++.1
data.hns-equil  in.reaxc.hns     log.8Mar18.reaxc.hns.g++.4
End of file listing, if you see nothing above there are no files.
flux R encode --hosts=flux-sample-[0-63] 

📦 Resources
{"version": 1, "execution": {"R_lite": [{"rank": "0-63", "children": {"core": "0-55"}}], "starttime": 0.0, "expiration": 0.0, "nodelist": ["flux-sample-[0-63]"]}}

🐸 Diagnostics: false
🚩️ Flux Option Flags defined

🦊 Independent Minister of Privilege
[exec]
allowed-users = [ "flux", "root" ]
allowed-shells = [ "/opt/view/libexec/flux/flux-shell" ]

🐸 Broker Configuration
# Flux needs to know the path to the IMP executable
[exec]
imp = "/opt/view/libexec/flux/flux-imp"

[access]
allow-guest-user = true
allow-root-owner = true

# Point to resource definition generated with flux-R(1).
[resource]
path = "/etc/flux/system/R"

[bootstrap]
curve_cert = "/etc/curve/curve.cert"
default_port = 8050
default_bind = "tcp://eth0:%p"
default_connect = "tcp://%h.flux-service.flux-operator.svc.cluster.local:%p"
hosts = [
        { host="flux-sample-[0-63]"},
]

[archive]
dbpath = "/var/lib/flux/job-archive.sqlite"
period = "1m"
busytimeout = "50s"chmod: cannot access '/opt/view/libexec/flux/flux-imp': No such file or directory
chmod: cannot access '/opt/view/libexec/flux/flux-imp': No such file or directory

🧊️ State Directory:
total 0


🔒️ Working directory permissions:
total 96
-rwxrwxrwx 1 flux root  2517 May 13 19:29 README.txt
-rwxrwxrwx 1 flux root 54692 May 13 19:29 data.hns-equil
-rwxrwxrwx 1 flux root 13576 May 13 19:29 ffield.reax.hns
-rwxrwxrwx 1 flux root   870 May 13 19:29 in.reaxc.hns
-rwxrwxrwx 1 flux root  4172 May 13 19:29 log.8Mar18.reaxc.hns.g++.1
-rwxrwxrwx 1 flux root  4168 May 13 19:29 log.8Mar18.reaxc.hns.g++.4


✨ Curve certificate generated by helper pod
#   ****  Generated on 2023-04-26 22:54:42 by CZMQ  ****
#   ZeroMQ CURVE **Secret** Certificate
#   DO NOT PROVIDE THIS FILE TO OTHER USERS nor change its permissions.
    
metadata
    name = "flux-cert-generator"
    keygen.hostname = "flux-sample-0"
curve
    public-key = "Px9Vyl#tp$58xOE@a1c@k[YYjFuy^x9hT%*rzi]^"
    secret-key = "Q4d7CPWC0MvbDt1lr8QPE03@W85Ds7@ptJj>K($o"
Extra command arguments are: 

🌀 sudo -u flux -E PYTHONPATH=/opt/view/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-pyrsistent-0.19.3-kbnsub7sugk32426tdippf4am733tcej/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-attrs-22.2.0-xxt3is4afn5dxqljxjw4c64grd5yrzl5/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-pycparser-2.21-uddpec2romvwc2poyrre7bj5qbp4jqwn/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-pyyaml-6.0-pdxwbzb2hyrgpx3bjkqizd77aoszdvbj/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-ply-3.11-k37gmnzkv6vavrjwznzws52zoswlirqa/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-jsonschema-4.17.3-audfdhc6xlie6ntzer4tpd7d6rle3eyp/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-cffi-1.15.1-4u7dbmm4ezxthpnafkculdrjlo7dewop/lib/python3.10/site-packages -E PATH=/opt/view/bin:/opt/spack-environment/spack/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin -E FI_EFA_USE_DEVICE_RDMA=1 -E RDMAV_FORK_SAFE=1  flux broker --config-path /etc/flux/config -Scron.directory=/etc/flux/system/cron.d   -Stbon.fanout=256   -Srundir=/run/flux -Sbroker.rc2_none    -Sstatedir=/var/lib/flux   -Slocal-uri=local:///run/flux/local -Stbon.connect_timeout=5s  -Stbon.zmqdebug=1  -Slog-stderr-level=6    -Slog-stderr-mode=local
broker.info[0]: start: none->join 1.36166ms
broker.info[0]: parent-none: join->init 0.03196ms
cron.info[0]: synchronizing cron tasks to event heartbeat.pulse
job-manager.info[0]: restart: 0 jobs
job-manager.info[0]: restart: 0 running jobs
job-manager.info[0]: restart: checkpoint.job-manager not found
broker.info[0]: rc1.0: running /opt/software/linux-rocky8-x86_64/gcc-8.5.0/flux-core-0.49.0-i5mwkh7xzw3ncjsw5droepelbamdlsf5/etc/flux/rc1.d/02-cron
broker.info[0]: rc1.0: running /opt/view/etc/flux/rc1.d/01-sched-fluxion
sched-fluxion-resource.info[0]: version 0.27.0
sched-fluxion-resource.warning[0]: create_reader: allowlist unsupported
sched-fluxion-qmanager.info[0]: version 0.27.0
broker.info[0]: rc1.0: running /opt/view/etc/flux/rc1.d/02-cron
sched-fluxion-resource.info[0]: populate_resource_db: loaded resources from core's resource.acquire
broker.info[0]: rc1.0: /opt/software/linux-rocky8-x86_64/gcc-8.5.0/flux-core-0.49.0-i5mwkh7xzw3ncjsw5droepelbamdlsf5/etc/flux/rc1 Exited (rc=0) 1.4s
broker.info[0]: rc1-success: init->quorum 1.36264s
broker.info[0]: online: flux-sample-0 (ranks 0)
broker.err[0]: quorum delayed: waiting for flux-sample-[1-63] (rank 1-63)
broker.err[0]: quorum delayed: waiting for flux-sample-[1-63] (rank 1-63)
```

</details>

And then an example worker, which always reports that the service isn't known:

<details>

<summary>Example Worker Log</summary>

```console
Flux username: flux
flux user is already added.
flux user identifiers:
uid=1000(flux) gid=1000(flux) groups=1000(flux)

As Flux prefix for flux commands: sudo -u flux -E PYTHONPATH=/opt/view/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-pyrsistent-0.19.3-kbnsub7sugk32426tdippf4am733tcej/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-attrs-22.2.0-xxt3is4afn5dxqljxjw4c64grd5yrzl5/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-pycparser-2.21-uddpec2romvwc2poyrre7bj5qbp4jqwn/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-pyyaml-6.0-pdxwbzb2hyrgpx3bjkqizd77aoszdvbj/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-ply-3.11-k37gmnzkv6vavrjwznzws52zoswlirqa/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-jsonschema-4.17.3-audfdhc6xlie6ntzer4tpd7d6rle3eyp/lib/python3.10/site-packages:/opt/software/linux-rocky8-x86_64/gcc-8.5.0/py-cffi-1.15.1-4u7dbmm4ezxthpnafkculdrjlo7dewop/lib/python3.10/site-packages -E PATH=/opt/view/bin:/opt/spack-environment/spack/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin -E FI_EFA_USE_DEVICE_RDMA=1 -E RDMAV_FORK_SAFE=1

👋 Hello, I'm flux-sample-1
The main host is flux-sample-0
The working directory is /opt/lammps/examples/reaxff/HNS, contents include:
/opt/lammps/examples/reaxff/HNS:
README.txt      ffield.reax.hns  log.8Mar18.reaxc.hns.g++.1
data.hns-equil  in.reaxc.hns     log.8Mar18.reaxc.hns.g++.4
End of file listing, if you see nothing above there are no files.
flux R encode --hosts=flux-sample-[0-63] 

📦 Resources
{"version": 1, "execution": {"R_lite": [{"rank": "0-63", "children": {"core": "0-55"}}], "starttime": 0.0, "expiration": 0.0, "nodelist": ["flux-sample-[0-63]"]}}

🐸 Diagnostics: false
🚩️ Flux Option Flags defined

🦊 Independent Minister of Privilege
[exec]
allowed-users = [ "flux", "root" ]
allowed-shells = [ "/opt/view/libexec/flux/flux-shell" ]

🐸 Broker Configuration
# Flux needs to know the path to the IMP executable
[exec]
imp = "/opt/view/libexec/flux/flux-imp"

[access]
allow-guest-user = true
allow-root-owner = true

# Point to resource definition generated with flux-R(1).
[resource]
path = "/etc/flux/system/R"

[bootstrap]
curve_cert = "/etc/curve/curve.cert"
default_port = 8050
default_bind = "tcp://eth0:%p"
default_connect = "tcp://%h.flux-service.flux-operator.svc.cluster.local:%p"
hosts = [
        { host="flux-sample-[0-63]"},
]

[archive]
dbpath = "/var/lib/flux/job-archive.sqlite"
period = "1m"
busytimeout = "50s"chmod: cannot access '/opt/view/libexec/flux/flux-imp': No such file or directory
chmod: cannot access '/opt/view/libexec/flux/flux-imp': No such file or directory

🧊️ State Directory:
total 0


🔒️ Working directory permissions:
total 96
-rwxrwxrwx 1 flux root  2517 May 13 19:29 README.txt
-rwxrwxrwx 1 flux root 54692 May 13 19:29 data.hns-equil
-rwxrwxrwx 1 flux root 13576 May 13 19:29 ffield.reax.hns
-rwxrwxrwx 1 flux root   870 May 13 19:29 in.reaxc.hns
-rwxrwxrwx 1 flux root  4172 May 13 19:29 log.8Mar18.reaxc.hns.g++.1
-rwxrwxrwx 1 flux root  4168 May 13 19:29 log.8Mar18.reaxc.hns.g++.4


✨ Curve certificate generated by helper pod
#   ****  Generated on 2023-04-26 22:54:42 by CZMQ  ****
#   ZeroMQ CURVE **Secret** Certificate
#   DO NOT PROVIDE THIS FILE TO OTHER USERS nor change its permissions.
    
metadata
    name = "flux-cert-generator"
    keygen.hostname = "flux-sample-0"
curve
    public-key = "Px9Vyl#tp$58xOE@a1c@k[YYjFuy^x9hT%*rzi]^"
    secret-key = "Q4d7CPWC0MvbDt1lr8QPE03@W85Ds7@ptJj>K($o"

🌀  flux start -o --config /etc/flux/config -Scron.directory=/etc/flux/system/cron.d   -Stbon.fanout=256   -Srundir=/run/flux -Sbroker.rc2_none    -Sstatedir=/var/lib/flux   -Slocal-uri=local:///run/flux/local -Stbon.connect_timeout=5s  -Stbon.zmqdebug=1  -Slog-stderr-level=6    -Slog-stderr-mode=local
broker.err[1]: Warning: unable to resolve upstream peer flux-sample-0.flux-service.flux-operator.svc.cluster.local: Name or service not known
broker.info[1]: start: none->join 1.34825ms
```

</details>

I did wait about 5-10 minutes the first time and I'm convinced this isn't a "slow to start" thing -
there is something wrong with networking. It looks like the workers think they are started / connected
but the broker doesn't see anything at all. Note that there are logs for the pods and nodes in the [data](data)
folder.

Note that I finally got a cluster connected at size 8, and started running small tests, but hit this:

```
ƒsCmeSoh: 0.553s exception
ƒsCmeSoh: exception: type=exec note=ƒsCmeSoh.402 called PMIx_Abort (status=1): N/A
```