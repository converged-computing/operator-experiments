# Canopie Experiments

This was my first effort where I was thinking of reproducing canopie exactly, but ran into an architecture issue (core dumped) and now I'm not sure if we want to use the MPI operator, period. I would prefer an updated strategy that uses the Flux Operator. 

## MPI Operator

We aren't going to use the Python template script, but rather just install the operator.
Install the MPI operator first:

```bash
kubectl apply -f ./experiments/mpi-operator.yaml
```

### Taints

The next step has us tainting nodes with the label fluence ([done here](https://github.com/flux-framework/flux-k8s/blob/e4b2dc20c095ba95a7217065349e30ee9bb34723/canopie22-artifacts/kube_setup/eks-efa-cluster-config.yaml#L34)). We will do that for now to reproduce the MPI operator, but when we change to the Flux operator we won't need to do that. We also aren't creating nodes with eksctl so we don't have labels, so we are going to manually hack it for now. From [here](https://github.com/flux-framework/flux-k8s/blob/canopie22-artifacts/canopie22-artifacts/kube_setup/eks-efa-cluster-config.yaml) we can see there are 32 workers and 2 launchers, so let's do 1 launcher and 3 workers. E.g., 4 nodes:

```bash
NAME                                          STATUS   ROLES    AGE   VERSION
gke-test-cluster-default-pool-92dbd7e9-bgv5   Ready    <none>   21m   v1.27.3-gke.100
gke-test-cluster-default-pool-92dbd7e9-h4sc   Ready    <none>   21m   v1.27.3-gke.100
gke-test-cluster-default-pool-92dbd7e9-ln89   Ready    <none>   21m   v1.27.3-gke.100
gke-test-cluster-default-pool-92dbd7e9-xzb4   Ready    <none>   21m   v1.27.3-gke.100
```

Note that I decided to not do this, because I don't care if the scheduling is a bit wonky for this test.
But you theoretically could choose one for the launcher and give the same taints / labels:

```bash
launcher=gke-test-cluster-default-pool-92dbd7e9-bgv5
kubectl taint nodes $launcher launcher=true:NoSchedule-
```

Do the same for the workers, but as a worker:

```bash
kubectl taint nodes gke-test-cluster-default-pool-92dbd7e9-h4sc worker=true:NoSchedule-
kubectl taint nodes gke-test-cluster-default-pool-92dbd7e9-ln89 worker=true:NoSchedule-
kubectl taint nodes gke-test-cluster-default-pool-92dbd7e9-xzb4 worker=true:NoSchedule-
```

The original script to taint is [here](https://github.com/flux-framework/flux-k8s/blob/canopie22-artifacts/canopie22-artifacts/kube_setup/taint_workers.sh) and the labels from eksctl are [here](https://github.com/flux-framework/flux-k8s/blob/canopie22-artifacts/canopie22-artifacts/kube_setup/eks-efa-cluster-config.yaml)

### Dummy Experiment Run

We next want to proceed to try the [experiments here](https://github.com/flux-framework/flux-k8s/tree/canopie22-artifacts/canopie22-artifacts). We are [starting here](https://github.com/flux-framework/flux-k8s/tree/canopie22-artifacts/canopie22-artifacts#running-experiments-with-amg-lammps-and-qmcpack). For provenance, I have cloned and copied the Dockerfile and yaml here and refactored them from templates into just yaml.

 - [experiments](experiments)
  - [lammps](experiments/lammps)

We can largely use the same containers referenced in the yamls. For example:

```bash
cd experiments/lammps

# run a small 2x2x2 problem on 12 processes
kubectl apply -f lammps_mpijob.yaml
```

Note some changes detailed [here](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master/pkg/coscheduling#podgroup) about PodGroup (that are reflected in the lammps yaml above).
Note that I got some errors in the launcher:

```bash
kubectl logs lammps-launcher-xxxx
```
```console
++ unset i
+ mpirun --allow-run-as-root --mca orte_launch_agent /opt/view/bin/orted --mca plm_rsh_agent rsh -x PATH -x LD_LIBRARY_PATH -np 12 --map-by socket lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
bash: line 1:     8 Illegal instruction     (core dumped) mpirun --allow-run-as-root --mca orte_launch_agent /opt/view/bin/orted --mca plm_rsh_agent rsh -x PATH -x LD_LIBRARY_PATH -np 12 --map-by socket lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
real 0.01
user 0.00
sys 0.01
```

And the workers logically did not do anything interesting:

```bash
kubectl logs lammps-worker-0
```
```console
Server listening on 0.0.0.0 port 22.
Server listening on :: port 22.
kex_exchange_identification: Connection closed by remote host
```

I tried an interactive test to see if I could run something, and it seems that there is some issue with this container on the node possibly? A basic lammps run did not work.

```bash
docker run -it milroy1/kf-testing:lammps-focal-openmpi-4.1.2 bash
```
```console
# ./lmp -v x 2 -v y 2 -v z 2 -in in.reaxc.hns -nocite
Illegal instruction (core dumped)
```

So that is a good stopping point. My suggestions for next steps are to:

- Decide if we want to use the MPI operator (or switch to the Flux Operator)
- Rebuild base containers with updated versions of things
- Re-do an experiment with these updates.

