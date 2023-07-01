# Testing Kueue

This is going to evaluate Kueue in the context of running the Flux Operator
(and then possibly integrating other KubeFlow pipelines and components that we like).

## Usage

### Create Cluster

Create a cluster with kind and install Kueue [using these instructions](https://kueue.sigs.k8s.io/docs/installation/)

```bash
kind create cluster
```
```bash
VERSION=v0.3.2
kubectl apply -f https://github.com/kubernetes-sigs/kueue/releases/download/$VERSION/manifests.yaml
```

### Concepts

Check out the [concepts page](https://kueue.sigs.k8s.io/docs/concepts/) to understand how kueue manages the user namespace.
Note that [additional RBAC](https://kueue.sigs.k8s.io/docs/tasks/rbac/) can be used to further define role.
We will use the default that are provided for an admin vs. user.

### Queues

We are going to follow the instructions [here](https://kueue.sigs.k8s.io/docs/tasks/administer_cluster_quotas/)
to create different cluster queues.

```bash
$ kubectl apply -f single-clusterqueue-setup.yaml
```

Note that we also might want to enable [waiting for pods to be ready](https://kueue.sigs.k8s.io/docs/tasks/setup_sequential_admission/)
but I didn't for this test. Once you have applied the yaml, check that the user-queue is ready:

```bash
$ kubectl get queues
NAME         CLUSTERQUEUE    PENDING WORKLOADS   ADMITTED WORKLOADS
user-queue   cluster-queue   0                   0
```

### Flux MiniCluster

Install the Flux Operator:

```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/main/examples/dist/flux-operator.yaml
```

To see logs if needed (and you'll want to wait until you see the operator running):

```bash
$ kubectl logs -n operator-system operator-controller-manager-65d89d4ffb-cfxrn 
```

Then create the MiniCluster. 

```bash
$ kubectl create -f minicluster.yaml
```

This part:

```yaml
  jobLabels:
    kueue.x-k8s.io/queue-name: user-queue
```

Indicates that it is controlled by queue. We can see the workflow is admitted:

```bash
$ kubectl get queues
NAME         CLUSTERQUEUE    PENDING WORKLOADS   ADMITTED WORKLOADS
user-queue   cluster-queue   0                   1
```

We can also look at workloads:

```bash
$ kubectl -n default get workloads
NAME                                QUEUE        ADMITTED BY     AGE
job-flux-sample-kueue-6sd5z-84717   user-queue   cluster-queue   62s
```

Or try the same with describe:

<details>

<summary>Describe Output</summary>

```bash
Name:         job-flux-sample-kueue-6sd5z-84717
Namespace:    default
Labels:       <none>
Annotations:  <none>
API Version:  kueue.x-k8s.io/v1beta1
Kind:         Workload
Metadata:
  Creation Timestamp:  2023-07-01T23:15:57Z
  Generation:          1
  Managed Fields:
    API Version:  kueue.x-k8s.io/v1beta1
    Fields Type:  FieldsV1
    fieldsV1:
      f:status:
        f:admission:
          f:clusterQueue:
          f:podSetAssignments:
            k:{"name":"main"}:
              .:
              f:flavors:
                f:cpu:
                f:memory:
              f:name:
              f:resourceUsage:
                f:cpu:
                f:memory:
        f:conditions:
          k:{"type":"Admitted"}:
            .:
            f:lastTransitionTime:
            f:message:
            f:reason:
            f:status:
            f:type:
    Manager:      kueue-admission
    Operation:    Apply
    Subresource:  status
    Time:         2023-07-01T23:15:57Z
    API Version:  kueue.x-k8s.io/v1beta1
    Fields Type:  FieldsV1
    fieldsV1:
      f:status:
        f:conditions:
          k:{"type":"Finished"}:
            .:
            f:lastTransitionTime:
            f:message:
            f:reason:
            f:status:
            f:type:
    Manager:      kueue-job-controller-Finished
    Operation:    Apply
    Subresource:  status
    Time:         2023-07-01T23:17:37Z
    API Version:  kueue.x-k8s.io/v1beta1
    Fields Type:  FieldsV1
    fieldsV1:
      f:metadata:
        f:ownerReferences:
          .:
          k:{"uid":"bdc16301-7681-4666-9b67-e59b0743de9d"}:
      f:spec:
        .:
        f:podSets:
          .:
          k:{"name":""}:
            .:
            f:count:
            f:name:
            f:template:
              .:
              f:metadata:
              f:spec:
                .:
                f:containers:
                f:dnsPolicy:
                f:restartPolicy:
                f:schedulerName:
                f:securityContext:
                f:setHostnameAsFQDN:
                f:subdomain:
                f:terminationGracePeriodSeconds:
                f:volumes:
        f:priority:
        f:queueName:
    Manager:    kueue
    Operation:  Update
    Time:       2023-07-01T23:15:57Z
  Owner References:
    API Version:           batch/v1
    Block Owner Deletion:  true
    Controller:            true
    Kind:                  Job
    Name:                  flux-sample-kueue-6sd5z
    UID:                   bdc16301-7681-4666-9b67-e59b0743de9d
  Resource Version:        4946
  UID:                     45be39c7-55ac-4245-87a7-0f5d358758d5
Spec:
  Pod Sets:
    Count:  1
    Name:   main
    Template:
      Metadata:
      Spec:
        Containers:
          Command:
            /bin/bash
            /flux_operator/wait-0.sh
            sleep 10
          Image:              ghcr.io/flux-framework/flux-restful-api:latest
          Image Pull Policy:  IfNotPresent
          Lifecycle:
          Name:  flux-sample-kueue-6sd5z
          Ports:
            Container Port:  5000
            Protocol:        TCP
          Resources:
            Requests:
              Cpu:     4
              Memory:  200Mi
          Security Context:
            Privileged:                false
          Stdin:                       true
          Termination Message Path:    /dev/termination-log
          Termination Message Policy:  File
          Tty:                         true
          Volume Mounts:
            Mount Path:  /mnt/curve/
            Name:        flux-sample-kueue-6sd5z-curve-mount
            Read Only:   true
            Mount Path:  /etc/flux/config
            Name:        flux-sample-kueue-6sd5z-flux-config
            Read Only:   true
            Mount Path:  /flux_operator/
            Name:        flux-sample-kueue-6sd5z-entrypoint
            Read Only:   true
        Dns Policy:      ClusterFirst
        Restart Policy:  OnFailure
        Scheduler Name:  default-scheduler
        Security Context:
        Set Hostname As FQDN:              false
        Subdomain:                         flux-service
        Termination Grace Period Seconds:  30
        Volumes:
          Config Map:
            Default Mode:  420
            Items:
              Key:   hostfile
              Path:  broker.toml
            Name:    flux-sample-kueue-6sd5z-flux-config
          Name:      flux-sample-kueue-6sd5z-flux-config
          Config Map:
            Default Mode:  420
            Items:
              Key:   wait-0
              Mode:  511
              Path:  wait-0.sh
            Name:    flux-sample-kueue-6sd5z-entrypoint
          Name:      flux-sample-kueue-6sd5z-entrypoint
          Config Map:
            Default Mode:  420
            Name:          flux-sample-kueue-6sd5z-curve-mount
          Name:            flux-sample-kueue-6sd5z-curve-mount
  Priority:                0
  Queue Name:              user-queue
Status:
  Admission:
    Cluster Queue:  cluster-queue
    Pod Set Assignments:
      Flavors:
        Cpu:     default-flavor
        Memory:  default-flavor
      Name:      main
      Resource Usage:
        Cpu:     4
        Memory:  200Mi
  Conditions:
    Last Transition Time:  2023-07-01T23:15:57Z
    Message:               Admitted by ClusterQueue cluster-queue
    Reason:                Admitted
    Status:                True
    Type:                  Admitted
    Last Transition Time:  2023-07-01T23:17:37Z
    Message:               Job finished successfully
    Reason:                JobFinished
    Status:                True
    Type:                  Finished
Events:
  Type    Reason    Age    From             Message
  ----    ------    ----   ----             -------
  Normal  Admitted  3m28s  kueue-admission  Admitted by ClusterQueue cluster-queue, wait time was 1s
```

</details>

You can see logs for the pod, which are very boring because we just ran sleep!

```bash
$ kubectl logs -n default flux-sample-kueue-6sd5z-0-6tvjz 
```
```console
...
broker.info[0]: start: none->join 1.47793ms
broker.info[0]: parent-none: join->init 0.048964ms
cron.info[0]: synchronizing cron tasks to event heartbeat.pulse
job-manager.info[0]: restart: 0 jobs
job-manager.info[0]: restart: 0 running jobs
job-manager.info[0]: restart: checkpoint.job-manager not found
broker.info[0]: rc1.0: running /etc/flux/rc1.d/01-sched-fluxion
sched-fluxion-resource.info[0]: version 0.27.0-15-gc90fbcc2
sched-fluxion-resource.warning[0]: create_reader: allowlist unsupported
sched-fluxion-resource.info[0]: populate_resource_db: loaded resources from core's resource.acquire
sched-fluxion-qmanager.info[0]: version 0.27.0-15-gc90fbcc2
broker.info[0]: rc1.0: running /etc/flux/rc1.d/02-cron
broker.info[0]: rc1.0: /etc/flux/rc1 Exited (rc=0) 0.5s
broker.info[0]: rc1-success: init->quorum 0.505636s
broker.info[0]: online: flux-sample-kueue-6sd5z-0 (ranks 0)
broker.info[0]: quorum-full: quorum->run 0.100838s
broker.info[0]: rc2.0: flux submit -N 1 -n 1 --quiet --watch sleep 10 Exited (rc=0) 10.3s
broker.info[0]: rc2-success: run->cleanup 10.324s
broker.info[0]: cleanup.0: flux queue stop --quiet --all --nocheckpoint Exited (rc=0) 0.1s
broker.info[0]: cleanup.1: flux cancel --user=all --quiet --states RUN Exited (rc=0) 0.1s
broker.info[0]: cleanup.2: flux queue idle --quiet Exited (rc=0) 0.1s
broker.info[0]: cleanup-success: cleanup->shutdown 0.269963s
broker.info[0]: children-none: shutdown->finalize 0.030092ms
broker.info[0]: rc3.0: running /etc/flux/rc3.d/01-sched-fluxion
broker.info[0]: rc3.0: /etc/flux/rc3 Exited (rc=0) 0.1s
broker.info[0]: rc3-success: finalize->goodbye 0.12544s
broker.info[0]: goodbye: goodbye->exit 0.026703ms
```

So I think my conclusions are that this is a layer to allow multi-tenancy,
and if we can programmatically access it via a workflow tool (that generates a dag
and can either define a Job, an MPIJob, or a Flux MiniCluster job), we could
have pretty nice support for running different kinds of workflows on Kubernetes.
Note that there are issues open for both [KubeFlow](https://github.com/kubernetes-sigs/kueue/issues/297)
and [Argo/Tekton](https://github.com/kubernetes-sigs/kueue/issues/74) so this seems like
it's taking a good direction to create Kubernetes batch objects, which is what we want.
The other direction (generating the requests for said objects from a DAG) is what I think
we need to tackle and experiment with.

### Clean Up

When you are done:

```bash
kind delete cluster
```
