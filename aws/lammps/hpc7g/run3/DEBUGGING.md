# Testing HPC7G with A Larger Problem Size

This log will include complete documentation that is being requested by AWS for debugging EFA.
We received two emails back with overlapping / slightly different requests, and I'll try to respond to
both. Here are the requests from the last sent email (that provided a nice bulleted list).

## eksctl create cluster

Since the current eksctl does not support hpc7g ARM, we are using a custom build from
from [this branch](https://github.com/weaveworks/eksctl/pull/6743#pullrequestreview-1507361538). 
Note that it has worked many times before, so we can rule this out. For:

> 1. eksctl create cluster command output (from starting to end) present in Terminal.

```
$ ./bin/eksctl create cluster -f ./config/eks-config.yaml
```

Here is the complete output.

```console
2023-07-28 10:53:59 [ℹ]  eksctl version 0.149.0-dev+2adbe4119.2023-07-15T12:17:52Z
2023-07-28 10:53:59 [ℹ]  using region us-east-1
2023-07-28 10:53:59 [ℹ]  subnets for us-east-1a - public:192.168.0.0/19 private:192.168.64.0/19
2023-07-28 10:53:59 [ℹ]  subnets for us-east-1b - public:192.168.32.0/19 private:192.168.96.0/19
2023-07-28 10:53:59 [ℹ]  nodegroup "workers" will use "" [AmazonLinux2/1.27]
2023-07-28 10:53:59 [ℹ]  using SSH public key "/home/vanessa/.ssh/id_eks.pub" as "eksctl-scaling-study-efa-nodegroup-workers-4e:93:d9:47:eb:81:3e:4f:1b:e0:44:ac:af:c6:ac:b3" 
2023-07-28 10:54:00 [ℹ]  using Kubernetes version 1.27
2023-07-28 10:54:00 [ℹ]  creating EKS cluster "scaling-study-efa" in "us-east-1" region with managed nodes
2023-07-28 10:54:00 [ℹ]  1 nodegroup (workers) was included (based on the include/exclude rules)
2023-07-28 10:54:00 [ℹ]  will create a CloudFormation stack for cluster itself and 0 nodegroup stack(s)
2023-07-28 10:54:00 [ℹ]  will create a CloudFormation stack for cluster itself and 1 managed nodegroup stack(s)
2023-07-28 10:54:00 [ℹ]  if you encounter any issues, check CloudFormation console or try 'eksctl utils describe-stacks --region=us-east-1 --cluster=scaling-study-efa'
2023-07-28 10:54:00 [ℹ]  Kubernetes API endpoint access will use default of {publicAccess=true, privateAccess=false} for cluster "scaling-study-efa" in "us-east-1"
2023-07-28 10:54:00 [ℹ]  CloudWatch logging will not be enabled for cluster "scaling-study-efa" in "us-east-1"
2023-07-28 10:54:00 [ℹ]  you can enable it with 'eksctl utils update-cluster-logging --enable-types={SPECIFY-YOUR-LOG-TYPES-HERE (e.g. all)} --region=us-east-1 --cluster=scaling-study-efa'
2023-07-28 10:54:00 [ℹ]  
2 sequential tasks: { create cluster control plane "scaling-study-efa", 
    2 sequential sub-tasks: { 
        wait for control plane to become ready,
        create managed nodegroup "workers",
    } 
}
2023-07-28 10:54:00 [ℹ]  building cluster stack "eksctl-scaling-study-efa-cluster"
2023-07-28 10:54:01 [ℹ]  deploying stack "eksctl-scaling-study-efa-cluster"
2023-07-28 10:54:31 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 10:55:01 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 10:56:02 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 10:57:02 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 10:58:02 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 10:59:02 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 11:00:03 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 11:01:03 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 11:02:03 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 11:03:04 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 11:04:04 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-cluster"
2023-07-28 11:06:07 [ℹ]  building managed nodegroup stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 11:06:07 [ℹ]  skipping us-east-1b from selection because it doesn't support the following instance type(s): hpc7g.16xlarge
2023-07-28 11:06:07 [ℹ]  EFA requires all nodes be in a single subnet, arbitrarily choosing one: [subnet-0c4d2c53245231094]
2023-07-28 11:06:08 [ℹ]  deploying stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 11:06:08 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 11:06:38 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 11:07:23 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 11:08:31 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 11:09:19 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 11:10:54 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 11:10:54 [ℹ]  waiting for the control plane to become ready
2023-07-28 11:10:55 [✔]  saved kubeconfig as "/home/vanessa/.kube/config"
2023-07-28 11:10:55 [ℹ]  1 task: { install EFA device plugin }
W0728 11:10:55.900247 2233074 warnings.go:70] spec.template.metadata.annotations[scheduler.alpha.kubernetes.io/critical-pod]: non-functional in v1.16+; use the "priorityClassName" field instead
2023-07-28 11:10:55 [ℹ]  created "kube-system:DaemonSet.apps/aws-efa-k8s-device-plugin-daemonset"
2023-07-28 11:10:55 [ℹ]  as you have enabled EFA, the EFA device plugin was automatically installed.
2023-07-28 11:10:55 [✔]  all EKS cluster resources for "scaling-study-efa" have been created
2023-07-28 11:10:56 [ℹ]  nodegroup "workers" has 8 node(s)
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-0-161.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-2-130.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-2-48.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-23-9.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-25-136.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-25-169.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-27-250.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-31-107.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  waiting for at least 8 node(s) to become ready in "workers"
2023-07-28 11:10:56 [ℹ]  nodegroup "workers" has 8 node(s)
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-0-161.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-2-130.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-2-48.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-23-9.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-25-136.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-25-169.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-27-250.ec2.internal" is ready
2023-07-28 11:10:56 [ℹ]  node "ip-192-168-31-107.ec2.internal" is ready
2023-07-28 11:10:59 [ℹ]  kubectl command should work with "/home/vanessa/.kube/config", try 'kubectl get nodes'
2023-07-28 11:10:59 [✔]  EKS cluster "scaling-study-efa" in "us-east-1" region is ready
```

## Environment

> 2. Please confirm if you are using local machine or ec2 machine (from where you are running eksctl command)

I am working from a local machine that has permanent (not temporary) credentials.

## Cluster Config 

> 3. Have you used the same cluster config when it was working fine yesterday morning (as you mentioned)?

We are using the same cluster config that was previously working.

```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: scaling-study-efa
  region: us-east-1
  version: "1.27"

# TODO we need AL2_ARM_64
availabilityZones: ["us-east-1a", "us-east-1b"]
managedNodeGroups:
  - name: workers
    availabilityZones: ["us-east-1a"]
    instanceType: hpc7g.16xlarge
    # This should only be needed if we had a list to choose from
    #instanceSelector:
    #  cpuArchitecture: arm64 
    minSize: 8
    maxSize: 8
    efaEnabled: true
    placement:
      groupName: eks-efa-testing
    labels: { "flux-operator": "true" }
    ssh:
      allow: true
      publicKeyPath: ~/.ssh/id_eks.pub
```

## Document Link

> 4. Please confirm if you are following any document or resource or link, if yes, please share5. Kindly provide outline of all the steps you have taken for creating EKS cluster with EFA .

We have run experiments many times, and follow this general pattern that I'm writing about now to run eksctl
to create the cluster, and then inspect the daemonsets. This document is available as a gist [here](https://gist.github.com/vsoch/4661f90df92d1577c7daed4ca794e1ec).

## eks-efa-testing

This placement group was created last year, and has worked for (now published) experiments and experiments at Kubecon.
It is definitely created.

> 6. You have mentioned placement group ‘eks-efa-testing’ in cluster config, could you please confirm if you have created or mentioned eks-efa-testing placement group in ec2 side before mentioning in cluster config.

## Worker Node 

> 7. Please provide the EKS log collector script [4] for problematic worker node. If logs size exceeds 5 MB, please upload the logs on s3 uploader[5].

Using [this script](https://github.com/awslabs/amazon-eks-ami/tree/master/log-collector-script/linux):
First on a crashed node (ip-192-168-25-136):

```bash
ssh -o 'IdentitiesOnly yes' -i "/home/vanessa/.ssh/id_eks.pub" ec2-user@ec2-54-172-206-249.compute-1.amazonaws.com
```
```bash
curl -O https://raw.githubusercontent.com/awslabs/amazon-eks-ami/master/log-collector-script/linux/eks-log-collector.sh
sudo bash eks-log-collector.sh
```
And then copied to my local machine:

```bash
scp -o 'IdentitiesOnly yes' -i "/home/vanessa/.ssh/id_eks.pub" ec2-user@ec2-54-172-206-249.compute-1.amazonaws.com:/var/log/eks_i-081cafd3368ab4d44_2023-07-28_1746-UTC_0.7.6.tar.gz eks_i-081cafd3368ab4d44_2023-07-28_1746-UTC_0.7.6-broken-node.tar.gzu
```

And then for a working one (ip-192-168-23-9):

```bash
ssh -o 'IdentitiesOnly yes' -i "/home/vanessa/.ssh/id_eks.pub"  ec2-user@ec2-35-153-175-5.compute-1.amazonaws.com
```

I will provide these .tar.gz with my ticket.

```bash
curl -O https://raw.githubusercontent.com/awslabs/amazon-eks-ami/master/log-collector-script/linux/eks-log-collector.sh
sudo bash eks-log-collector.sh
```
And then copied to my local machine:

```bash
scp -o 'IdentitiesOnly yes' -i "/home/vanessa/.ssh/id_eks.pub" ec2-user@ec2-35-153-175-5.compute-1.amazonaws.com:/var/log/eks_i-0f2effa68088972f2_2023-07-28_1752-UTC_0.7.6.tar.gz eks_i-0f2effa68088972f2_2023-07-28_1752-UTC_0.7.6-working-node.tar.gz
```

## Command Output

> Also, Please provide the output of below commands:

> 1. eksctl version and aws --version command output

```bash
$ ./bin/eksctl version
0.149.0-dev+2adbe4119.2023-07-15T12:17:52Z
```
Go applications don't usually have a `--version`. This was built from [this branch](https://github.com/weaveworks/eksctl/pull/6743#pullrequestreview-1507361538).

> 2. kubectl describe ds aws-efa-k8s-device-plugin-daemonset -n <Namespace>

```bash
$ kubectl describe ds aws-efa-k8s-device-plugin-daemonset -n kube-system 
```
```console
Name:           aws-efa-k8s-device-plugin-daemonset
Selector:       name=aws-efa-k8s-device-plugin
Node-Selector:  <none>
Labels:         <none>
Annotations:    deprecated.daemonset.template.generation: 1
Desired Number of Nodes Scheduled: 8
Current Number of Nodes Scheduled: 8
Number of Nodes Scheduled with Up-to-date Pods: 8
Number of Nodes Scheduled with Available Pods: 3
Number of Nodes Misscheduled: 0
Pods Status:  8 Running / 0 Waiting / 0 Succeeded / 0 Failed
Pod Template:
  Labels:           name=aws-efa-k8s-device-plugin
  Annotations:      scheduler.alpha.kubernetes.io/critical-pod: 
  Service Account:  default
  Containers:
   aws-efa-k8s-device-plugin:
    Image:        602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3
    Port:         <none>
    Host Port:    <none>
    Environment:  <none>
    Mounts:
      /var/lib/kubelet/device-plugins from device-plugin (rw)
  Volumes:
   device-plugin:
    Type:               HostPath (bare host directory volume)
    Path:               /var/lib/kubelet/device-plugins
    HostPathType:       
  Priority Class Name:  system-node-critical
Events:
  Type    Reason            Age   From                  Message
  ----    ------            ----  ----                  -------
  Normal  SuccessfulCreate  14m   daemonset-controller  Created pod: aws-efa-k8s-device-plugin-daemonset-7tf47
  Normal  SuccessfulCreate  14m   daemonset-controller  Created pod: aws-efa-k8s-device-plugin-daemonset-29qlv
  Normal  SuccessfulCreate  14m   daemonset-controller  Created pod: aws-efa-k8s-device-plugin-daemonset-vc9gd
  Normal  SuccessfulCreate  14m   daemonset-controller  Created pod: aws-efa-k8s-device-plugin-daemonset-886vc
  Normal  SuccessfulCreate  14m   daemonset-controller  Created pod: aws-efa-k8s-device-plugin-daemonset-w7w7q
  Normal  SuccessfulCreate  14m   daemonset-controller  Created pod: aws-efa-k8s-device-plugin-daemonset-vbj2m
  Normal  SuccessfulCreate  14m   daemonset-controller  Created pod: aws-efa-k8s-device-plugin-daemonset-4kwqn
  Normal  SuccessfulCreate  14m   daemonset-controller  Created pod: aws-efa-k8s-device-plugin-daemonset-6d4g2
```

Json output included too:

```bash
$ kubectl get ds aws-efa-k8s-device-plugin-daemonset -n kube-system -o json
```
```console
{
    "apiVersion": "apps/v1",
    "kind": "DaemonSet",
    "metadata": {
        "annotations": {
            "deprecated.daemonset.template.generation": "1"
        },
        "creationTimestamp": "2023-07-28T17:10:55Z",
        "generation": 1,
        "name": "aws-efa-k8s-device-plugin-daemonset",
        "namespace": "kube-system",
        "resourceVersion": "2533",
        "uid": "64cbfeb6-f251-4797-8b92-07ef6c3a40db"
    },
    "spec": {
        "revisionHistoryLimit": 10,
        "selector": {
            "matchLabels": {
                "name": "aws-efa-k8s-device-plugin"
            }
        },
        "template": {
            "metadata": {
                "annotations": {
                    "scheduler.alpha.kubernetes.io/critical-pod": ""
                },
                "creationTimestamp": null,
                "labels": {
                    "name": "aws-efa-k8s-device-plugin"
                }
            },
            "spec": {
                "affinity": {
                    "nodeAffinity": {
                        "requiredDuringSchedulingIgnoredDuringExecution": {
                            "nodeSelectorTerms": [
                                {
                                    "matchExpressions": [
                                        {
                                            "key": "node.kubernetes.io/instance-type",
                                            "operator": "In",
                                            "values": [
                                                "c5n.18xlarge",
                                                "c5n.9xlarge",
                                                "c5n.metal",
                                                "c6a.32xlarge",
                                                "c6a.48xlarge",
                                                "c6a.metal",
                                                "c6gn.16xlarge",
                                                "c6i.32xlarge",
                                                "c6i.metal",
                                                "c6id.32xlarge",
                                                "c6id.metal",
                                                "dl1.24xlarge",
                                                "g4dn.12xlarge",
                                                "g4dn.8xlarge",
                                                "g4dn.metal",
                                                "g5.48xlarge",
                                                "hpc6a.48xlarge",
                                                "hpc7g.16xlarge",
                                                "hpc7g.8xlarge",
                                                "hpc7g.4xlarge",
                                                "i3en.12xlarge",
                                                "i3en.24xlarge",
                                                "i3en.metal",
                                                "i4i.32xlarge",
                                                "i4i.metal",
                                                "im4gn.16xlarge",
                                                "inf1.24xlarge",
                                                "m5dn.24xlarge",
                                                "m5dn.metal",
                                                "m5n.24xlarge",
                                                "m5n.metal",
                                                "m5zn.12xlarge",
                                                "m5zn.metal",
                                                "m6a.32xlarge",
                                                "m6a.48xlarge",
                                                "m6a.metal",
                                                "m6i.32xlarge",
                                                "m6i.metal",
                                                "m6id.32xlarge",
                                                "m6id.metal",
                                                "p3dn.24xlarge",
                                                "p4d.24xlarge",
                                                "p4de.24xlarge",
                                                "r5dn.24xlarge",
                                                "r5dn.metal",
                                                "r5n.24xlarge",
                                                "r5n.metal",
                                                "r6i.32xlarge",
                                                "r6i.metal",
                                                "vt1.24xlarge",
                                                "x2idn.32xlarge",
                                                "x2idn.metal",
                                                "x2iedn.32xlarge",
                                                "x2iedn.metal",
                                                "x2iezn.12xlarge",
                                                "x2iezn.metal"
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "matchExpressions": [
                                        {
                                            "key": "node.kubernetes.io/instance-type",
                                            "operator": "In",
                                            "values": [
                                                "c5n.18xlarge",
                                                "c5n.9xlarge",
                                                "c5n.metal",
                                                "c6a.32xlarge",
                                                "c6a.48xlarge",
                                                "c6a.metal",
                                                "c6gn.16xlarge",
                                                "c6i.32xlarge",
                                                "c6i.metal",
                                                "c6id.32xlarge",
                                                "c6id.metal",
                                                "dl1.24xlarge",
                                                "g4dn.12xlarge",
                                                "g4dn.8xlarge",
                                                "g4dn.metal",
                                                "g5.48xlarge",
                                                "hpc6a.48xlarge",
                                                "hpc7g.16xlarge",
                                                "hpc7g.8xlarge",
                                                "hpc7g.4xlarge",
                                                "i3en.12xlarge",
                                                "i3en.24xlarge",
                                                "i3en.metal",
                                                "i4i.32xlarge",
                                                "i4i.metal",
                                                "im4gn.16xlarge",
                                                "inf1.24xlarge",
                                                "m5dn.24xlarge",
                                                "m5dn.metal",
                                                "m5n.24xlarge",
                                                "m5n.metal",
                                                "m5zn.12xlarge",
                                                "m5zn.metal",
                                                "m6a.32xlarge",
                                                "m6a.48xlarge",
                                                "m6a.metal",
                                                "m6i.32xlarge",
                                                "m6i.metal",
                                                "m6id.32xlarge",
                                                "m6id.metal",
                                                "p3dn.24xlarge",
                                                "p4d.24xlarge",
                                                "p4de.24xlarge",
                                                "r5dn.24xlarge",
                                                "r5dn.metal",
                                                "r5n.24xlarge",
                                                "r5n.metal",
                                                "r6i.32xlarge",
                                                "r6i.metal",
                                                "vt1.24xlarge",
                                                "x2idn.32xlarge",
                                                "x2idn.metal",
                                                "x2iedn.32xlarge",
                                                "x2iedn.metal",
                                                "x2iezn.12xlarge",
                                                "x2iezn.metal"
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
                "containers": [
                    {
                        "image": "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3",
                        "imagePullPolicy": "IfNotPresent",
                        "name": "aws-efa-k8s-device-plugin",
                        "resources": {},
                        "securityContext": {
                            "allowPrivilegeEscalation": false,
                            "capabilities": {
                                "drop": [
                                    "ALL"
                                ]
                            }
                        },
                        "terminationMessagePath": "/dev/termination-log",
                        "terminationMessagePolicy": "File",
                        "volumeMounts": [
                            {
                                "mountPath": "/var/lib/kubelet/device-plugins",
                                "name": "device-plugin"
                            }
                        ]
                    }
                ],
                "dnsPolicy": "ClusterFirst",
                "hostNetwork": true,
                "priorityClassName": "system-node-critical",
                "restartPolicy": "Always",
                "schedulerName": "default-scheduler",
                "securityContext": {},
                "serviceAccount": "default",
                "serviceAccountName": "default",
                "terminationGracePeriodSeconds": 30,
                "tolerations": [
                    {
                        "key": "CriticalAddonsOnly",
                        "operator": "Exists"
                    },
                    {
                        "effect": "NoSchedule",
                        "key": "aws.amazon.com/efa",
                        "operator": "Exists"
                    }
                ],
                "volumes": [
                    {
                        "hostPath": {
                            "path": "/var/lib/kubelet/device-plugins",
                            "type": ""
                        },
                        "name": "device-plugin"
                    }
                ]
            }
        },
        "updateStrategy": {
            "rollingUpdate": {
                "maxSurge": 0,
                "maxUnavailable": 1
            },
            "type": "RollingUpdate"
        }
    },
    "status": {
        "currentNumberScheduled": 8,
        "desiredNumberScheduled": 8,
        "numberAvailable": 3,
        "numberMisscheduled": 0,
        "numberReady": 3,
        "numberUnavailable": 5,
        "observedGeneration": 1,
        "updatedNumberScheduled": 8
    }
}

```

> 3. kubectl describe pod <aws-efa-k8s-device-plugin-daemonset with crashloopbackOff error> -n <Namespace>


Here are all pods with wide:

```bash
$ kubectl get pods -n kube-system -o wide
```
```console
NAME                                        READY   STATUS             RESTARTS        AGE   IP               NODE                             NOMINATED NODE   READINESS GATES
aws-efa-k8s-device-plugin-daemonset-29qlv   1/1     Running            0               15m   192.168.0.161    ip-192-168-0-161.ec2.internal    <none>           <none>
aws-efa-k8s-device-plugin-daemonset-4kwqn   0/1     CrashLoopBackOff   7 (4m42s ago)   15m   192.168.25.169   ip-192-168-25-169.ec2.internal   <none>           <none>
aws-efa-k8s-device-plugin-daemonset-6d4g2   0/1     CrashLoopBackOff   7 (4m38s ago)   15m   192.168.2.130    ip-192-168-2-130.ec2.internal    <none>           <none>
aws-efa-k8s-device-plugin-daemonset-7tf47   1/1     Running            0               15m   192.168.23.9     ip-192-168-23-9.ec2.internal     <none>           <none>
aws-efa-k8s-device-plugin-daemonset-886vc   0/1     CrashLoopBackOff   7 (4m39s ago)   15m   192.168.27.250   ip-192-168-27-250.ec2.internal   <none>           <none>
aws-efa-k8s-device-plugin-daemonset-vbj2m   0/1     CrashLoopBackOff   7 (4m45s ago)   15m   192.168.31.107   ip-192-168-31-107.ec2.internal   <none>           <none>
aws-efa-k8s-device-plugin-daemonset-vc9gd   1/1     Running            0               15m   192.168.2.48     ip-192-168-2-48.ec2.internal     <none>           <none>
aws-efa-k8s-device-plugin-daemonset-w7w7q   0/1     CrashLoopBackOff   7 (4m39s ago)   15m   192.168.25.136   ip-192-168-25-136.ec2.internal   <none>           <none>
aws-node-5jhct                              1/1     Running            0               17m   192.168.0.161    ip-192-168-0-161.ec2.internal    <none>           <none>
aws-node-7mltl                              1/1     Running            0               17m   192.168.31.107   ip-192-168-31-107.ec2.internal   <none>           <none>
aws-node-7v5c4                              1/1     Running            0               17m   192.168.27.250   ip-192-168-27-250.ec2.internal   <none>           <none>
aws-node-cgkl5                              1/1     Running            0               17m   192.168.2.48     ip-192-168-2-48.ec2.internal     <none>           <none>
aws-node-n8bd8                              1/1     Running            0               17m   192.168.25.169   ip-192-168-25-169.ec2.internal   <none>           <none>
aws-node-t64xt                              1/1     Running            0               17m   192.168.2.130    ip-192-168-2-130.ec2.internal    <none>           <none>
aws-node-wv427                              1/1     Running            0               17m   192.168.23.9     ip-192-168-23-9.ec2.internal     <none>           <none>
aws-node-zvj5m                              1/1     Running            0               17m   192.168.25.136   ip-192-168-25-136.ec2.internal   <none>           <none>
coredns-79df7fff65-h8r76                    1/1     Running            0               25m   192.168.23.238   ip-192-168-31-107.ec2.internal   <none>           <none>
coredns-79df7fff65-khlbc                    1/1     Running            0               25m   192.168.17.58    ip-192-168-31-107.ec2.internal   <none>           <none>
kube-proxy-64gxx                            1/1     Running            0               17m   192.168.31.107   ip-192-168-31-107.ec2.internal   <none>           <none>
kube-proxy-89s9q                            1/1     Running            0               17m   192.168.2.130    ip-192-168-2-130.ec2.internal    <none>           <none>
kube-proxy-f5jh6                            1/1     Running            0               17m   192.168.25.136   ip-192-168-25-136.ec2.internal   <none>           <none>
kube-proxy-gtz9z                            1/1     Running            0               17m   192.168.2.48     ip-192-168-2-48.ec2.internal     <none>           <none>
kube-proxy-n7mnk                            1/1     Running            0               17m   192.168.25.169   ip-192-168-25-169.ec2.internal   <none>           <none>
kube-proxy-ngnss                            1/1     Running            0               17m   192.168.0.161    ip-192-168-0-161.ec2.internal    <none>           <none>
kube-proxy-swdlq                            1/1     Running            0               17m   192.168.23.9     ip-192-168-23-9.ec2.internal     <none>           <none>
kube-proxy-ztdtj                            1/1     Running            0               17m   192.168.27.250   ip-192-168-27-250.ec2.internal   <none>           <none>
```

### Crashing Pod

And for a crashing pod, describe and json output:

```bash
$ kubectl describe pods -n kube-system  aws-efa-k8s-device-plugin-daemonset-4kwqn
```
```console
Name:                 aws-efa-k8s-device-plugin-daemonset-4kwqn
Namespace:            kube-system
Priority:             2000001000
Priority Class Name:  system-node-critical
Service Account:      default
Node:                 ip-192-168-25-169.ec2.internal/192.168.25.169
Start Time:           Fri, 28 Jul 2023 11:10:56 -0600
Labels:               controller-revision-hash=5bc5db57b
                      name=aws-efa-k8s-device-plugin
                      pod-template-generation=1
Annotations:          scheduler.alpha.kubernetes.io/critical-pod: 
Status:               Running
IP:                   192.168.25.169
IPs:
  IP:           192.168.25.169
Controlled By:  DaemonSet/aws-efa-k8s-device-plugin-daemonset
Containers:
  aws-efa-k8s-device-plugin:
    Container ID:   containerd://82f21d4c8433d004b84c3b2c496dca30156bd3370474f42bf6f672526c5fee7d
    Image:          602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3
    Image ID:       602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin@sha256:364d46e3e482f7cd03c586a69996348aa0ec8e6ff711d73013fbfba1ceb0b20d
    Port:           <none>
    Host Port:      <none>
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Completed
      Exit Code:    0
      Started:      Fri, 28 Jul 2023 11:27:06 -0600
      Finished:     Fri, 28 Jul 2023 11:27:06 -0600
    Ready:          False
    Restart Count:  8
    Environment:    <none>
    Mounts:
      /var/lib/kubelet/device-plugins from device-plugin (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-552rx (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             False 
  ContainersReady   False 
  PodScheduled      True 
Volumes:
  device-plugin:
    Type:          HostPath (bare host directory volume)
    Path:          /var/lib/kubelet/device-plugins
    HostPathType:  
  kube-api-access-552rx:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    ConfigMapOptional:       <nil>
    DownwardAPI:             true
QoS Class:                   BestEffort
Node-Selectors:              <none>
Tolerations:                 CriticalAddonsOnly op=Exists
                             aws.amazon.com/efa:NoSchedule op=Exists
                             node.kubernetes.io/disk-pressure:NoSchedule op=Exists
                             node.kubernetes.io/memory-pressure:NoSchedule op=Exists
                             node.kubernetes.io/network-unavailable:NoSchedule op=Exists
                             node.kubernetes.io/not-ready:NoExecute op=Exists
                             node.kubernetes.io/pid-pressure:NoSchedule op=Exists
                             node.kubernetes.io/unreachable:NoExecute op=Exists
                             node.kubernetes.io/unschedulable:NoSchedule op=Exists
Events:
  Type     Reason     Age                  From               Message
  ----     ------     ----                 ----               -------
  Normal   Scheduled  16m                  default-scheduler  Successfully assigned kube-system/aws-efa-k8s-device-plugin-daemonset-4kwqn to ip-192-168-25-169.ec2.internal
  Normal   Pulling    16m                  kubelet            Pulling image "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3"
  Normal   Pulled     16m                  kubelet            Successfully pulled image "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3" in 5.895362929s (5.895378505s including waiting)
  Normal   Created    15m (x5 over 16m)    kubelet            Created container aws-efa-k8s-device-plugin
  Normal   Pulled     15m (x4 over 16m)    kubelet            Container image "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3" already present on machine
  Normal   Started    15m (x5 over 16m)    kubelet            Started container aws-efa-k8s-device-plugin
  Warning  BackOff    107s (x71 over 16m)  kubelet            Back-off restarting failed container aws-efa-k8s-device-plugin in pod aws-efa-k8s-device-plugin-daemonset-4kwqn_kube-system(3e6d6f0c-ba33-4953-9b7c-556bd24df96f)
```

And logs for this crashing pod:

```bash
$ kubectl logs -n kube-system  aws-efa-k8s-device-plugin-daemonset-4kwqn
2023/07/28 17:27:06 Fetching EFA devices.
2023/07/28 17:27:06 No devices found.
```

### Working Pod

These are describe, json, and logs from a working pod (what it should look like):

```bash
$ kubectl describe pods -n kube-system aws-efa-k8s-device-plugin-daemonset-vc9gd
```
```console
Name:                 aws-efa-k8s-device-plugin-daemonset-vc9gd
Namespace:            kube-system
Priority:             2000001000
Priority Class Name:  system-node-critical
Service Account:      default
Node:                 ip-192-168-2-48.ec2.internal/192.168.2.48
Start Time:           Fri, 28 Jul 2023 11:10:56 -0600
Labels:               controller-revision-hash=5bc5db57b
                      name=aws-efa-k8s-device-plugin
                      pod-template-generation=1
Annotations:          scheduler.alpha.kubernetes.io/critical-pod: 
Status:               Running
IP:                   192.168.2.48
IPs:
  IP:           192.168.2.48
Controlled By:  DaemonSet/aws-efa-k8s-device-plugin-daemonset
Containers:
  aws-efa-k8s-device-plugin:
    Container ID:   containerd://33eb057fa9ea999aa20fa7a35353564a04b12abe4c0b0f1397e47a9bcf77c37b
    Image:          602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3
    Image ID:       602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin@sha256:364d46e3e482f7cd03c586a69996348aa0ec8e6ff711d73013fbfba1ceb0b20d
    Port:           <none>
    Host Port:      <none>
    State:          Running
      Started:      Fri, 28 Jul 2023 11:11:02 -0600
    Ready:          True
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/lib/kubelet/device-plugins from device-plugin (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-qn9zs (ro)
Conditions:
  Type              Status
  Initialized       True 
  Ready             True 
  ContainersReady   True 
  PodScheduled      True 
Volumes:
  device-plugin:
    Type:          HostPath (bare host directory volume)
    Path:          /var/lib/kubelet/device-plugins
    HostPathType:  
  kube-api-access-qn9zs:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    ConfigMapOptional:       <nil>
    DownwardAPI:             true
QoS Class:                   BestEffort
Node-Selectors:              <none>
Tolerations:                 CriticalAddonsOnly op=Exists
                             aws.amazon.com/efa:NoSchedule op=Exists
                             node.kubernetes.io/disk-pressure:NoSchedule op=Exists
                             node.kubernetes.io/memory-pressure:NoSchedule op=Exists
                             node.kubernetes.io/network-unavailable:NoSchedule op=Exists
                             node.kubernetes.io/not-ready:NoExecute op=Exists
                             node.kubernetes.io/pid-pressure:NoSchedule op=Exists
                             node.kubernetes.io/unreachable:NoExecute op=Exists
                             node.kubernetes.io/unschedulable:NoSchedule op=Exists
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  22m   default-scheduler  Successfully assigned kube-system/aws-efa-k8s-device-plugin-daemonset-vc9gd to ip-192-168-2-48.ec2.internal
  Normal  Pulling    22m   kubelet            Pulling image "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3"
  Normal  Pulled     22m   kubelet            Successfully pulled image "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3" in 6.029613433s (6.029625785s including waiting)
  Normal  Created    22m   kubelet            Created container aws-efa-k8s-device-plugin
  Normal  Started    22m   kubelet            Started container aws-efa-k8s-device-plugin
```

And here is json output for a working pod:

```bash
$ kubectl get pods -n kube-system aws-efa-k8s-device-plugin-daemonset-vc9gd -o json
```
```console
{
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "annotations": {
            "scheduler.alpha.kubernetes.io/critical-pod": ""
        },
        "creationTimestamp": "2023-07-28T17:10:56Z",
        "generateName": "aws-efa-k8s-device-plugin-daemonset-",
        "labels": {
            "controller-revision-hash": "5bc5db57b",
            "name": "aws-efa-k8s-device-plugin",
            "pod-template-generation": "1"
        },
        "name": "aws-efa-k8s-device-plugin-daemonset-vc9gd",
        "namespace": "kube-system",
        "ownerReferences": [
            {
                "apiVersion": "apps/v1",
                "blockOwnerDeletion": true,
                "controller": true,
                "kind": "DaemonSet",
                "name": "aws-efa-k8s-device-plugin-daemonset",
                "uid": "64cbfeb6-f251-4797-8b92-07ef6c3a40db"
            }
        ],
        "resourceVersion": "2416",
        "uid": "af7a7466-97b5-4af0-8914-35b30dc7a0f9"
    },
    "spec": {
        "affinity": {
            "nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {
                    "nodeSelectorTerms": [
                        {
                            "matchFields": [
                                {
                                    "key": "metadata.name",
                                    "operator": "In",
                                    "values": [
                                        "ip-192-168-2-48.ec2.internal"
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        },
        "containers": [
            {
                "image": "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3",
                "imagePullPolicy": "IfNotPresent",
                "name": "aws-efa-k8s-device-plugin",
                "resources": {},
                "securityContext": {
                    "allowPrivilegeEscalation": false,
                    "capabilities": {
                        "drop": [
                            "ALL"
                        ]
                    }
                },
                "terminationMessagePath": "/dev/termination-log",
                "terminationMessagePolicy": "File",
                "volumeMounts": [
                    {
                        "mountPath": "/var/lib/kubelet/device-plugins",
                        "name": "device-plugin"
                    },
                    {
                        "mountPath": "/var/run/secrets/kubernetes.io/serviceaccount",
                        "name": "kube-api-access-qn9zs",
                        "readOnly": true
                    }
                ]
            }
        ],
        "dnsPolicy": "ClusterFirst",
        "enableServiceLinks": true,
        "hostNetwork": true,
        "nodeName": "ip-192-168-2-48.ec2.internal",
        "preemptionPolicy": "PreemptLowerPriority",
        "priority": 2000001000,
        "priorityClassName": "system-node-critical",
        "restartPolicy": "Always",
        "schedulerName": "default-scheduler",
        "securityContext": {},
        "serviceAccount": "default",
        "serviceAccountName": "default",
        "terminationGracePeriodSeconds": 30,
        "tolerations": [
            {
                "key": "CriticalAddonsOnly",
                "operator": "Exists"
            },
            {
                "effect": "NoSchedule",
                "key": "aws.amazon.com/efa",
                "operator": "Exists"
            },
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/not-ready",
                "operator": "Exists"
            },
            {
                "effect": "NoExecute",
                "key": "node.kubernetes.io/unreachable",
                "operator": "Exists"
            },
            {
                "effect": "NoSchedule",
                "key": "node.kubernetes.io/disk-pressure",
                "operator": "Exists"
            },
            {
                "effect": "NoSchedule",
                "key": "node.kubernetes.io/memory-pressure",
                "operator": "Exists"
            },
            {
                "effect": "NoSchedule",
                "key": "node.kubernetes.io/pid-pressure",
                "operator": "Exists"
            },
            {
                "effect": "NoSchedule",
                "key": "node.kubernetes.io/unschedulable",
                "operator": "Exists"
            },
            {
                "effect": "NoSchedule",
                "key": "node.kubernetes.io/network-unavailable",
                "operator": "Exists"
            }
        ],
        "volumes": [
            {
                "hostPath": {
                    "path": "/var/lib/kubelet/device-plugins",
                    "type": ""
                },
                "name": "device-plugin"
            },
            {
                "name": "kube-api-access-qn9zs",
                "projected": {
                    "defaultMode": 420,
                    "sources": [
                        {
                            "serviceAccountToken": {
                                "expirationSeconds": 3607,
                                "path": "token"
                            }
                        },
                        {
                            "configMap": {
                                "items": [
                                    {
                                        "key": "ca.crt",
                                        "path": "ca.crt"
                                    }
                                ],
                                "name": "kube-root-ca.crt"
                            }
                        },
                        {
                            "downwardAPI": {
                                "items": [
                                    {
                                        "fieldRef": {
                                            "apiVersion": "v1",
                                            "fieldPath": "metadata.namespace"
                                        },
                                        "path": "namespace"
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        ]
    },
    "status": {
        "conditions": [
            {
                "lastProbeTime": null,
                "lastTransitionTime": "2023-07-28T17:10:56Z",
                "status": "True",
                "type": "Initialized"
            },
            {
                "lastProbeTime": null,
                "lastTransitionTime": "2023-07-28T17:11:03Z",
                "status": "True",
                "type": "Ready"
            },
            {
                "lastProbeTime": null,
                "lastTransitionTime": "2023-07-28T17:11:03Z",
                "status": "True",
                "type": "ContainersReady"
            },
            {
                "lastProbeTime": null,
                "lastTransitionTime": "2023-07-28T17:10:56Z",
                "status": "True",
                "type": "PodScheduled"
            }
        ],
        "containerStatuses": [
            {
                "containerID": "containerd://33eb057fa9ea999aa20fa7a35353564a04b12abe4c0b0f1397e47a9bcf77c37b",
                "image": "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3",
                "imageID": "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin@sha256:364d46e3e482f7cd03c586a69996348aa0ec8e6ff711d73013fbfba1ceb0b20d",
                "lastState": {},
                "name": "aws-efa-k8s-device-plugin",
                "ready": true,
                "restartCount": 0,
                "started": true,
                "state": {
                    "running": {
                        "startedAt": "2023-07-28T17:11:02Z"
                    }
                }
            }
        ],
        "hostIP": "192.168.2.48",
        "phase": "Running",
        "podIP": "192.168.2.48",
        "podIPs": [
            {
                "ip": "192.168.2.48"
            }
        ],
        "qosClass": "BestEffort",
        "startTime": "2023-07-28T17:10:56Z"
    }
}
```

And what the working logs look like:

```bash
$ kubectl logs -n kube-system aws-efa-k8s-device-plugin-daemonset-vc9gd
```
```console
2023/07/28 17:11:02 Fetching EFA devices.
2023/07/28 17:11:02 device: rdmap0s6,uverbs0,/sys/class/infiniband_verbs/uverbs0,/sys/class/infiniband/rdmap0s6

2023/07/28 17:11:02 EFA Device list: [{rdmap0s6 uverbs0 /sys/class/infiniband_verbs/uverbs0 /sys/class/infiniband/rdmap0s6}]
2023/07/28 17:11:02 Starting FS watcher.
2023/07/28 17:11:02 Starting OS watcher.
2023/07/28 17:11:02 device: rdmap0s6,uverbs0,/sys/class/infiniband_verbs/uverbs0,/sys/class/infiniband/rdmap0s6

2023/07/28 17:11:02 Starting to serve on /var/lib/kubelet/device-plugins/aws-efa-device-plugin.sock
2023/07/28 17:11:02 Registered device plugin with Kubelet
```

## Nodes

Here is output of a broken node:

```bash
$ kubectl get node ip-192-168-25-169.ec2.internal -o json
```
```console
{
    "apiVersion": "v1",
    "kind": "Node",
    "metadata": {
        "annotations": {
            "alpha.kubernetes.io/provided-node-ip": "192.168.25.169",
            "node.alpha.kubernetes.io/ttl": "0",
            "volumes.kubernetes.io/controller-managed-attach-detach": "true"
        },
        "creationTimestamp": "2023-07-28T17:08:48Z",
        "labels": {
            "alpha.eksctl.io/cluster-name": "scaling-study-efa",
            "alpha.eksctl.io/nodegroup-name": "workers",
            "beta.kubernetes.io/arch": "arm64",
            "beta.kubernetes.io/instance-type": "hpc7g.16xlarge",
            "beta.kubernetes.io/os": "linux",
            "eks.amazonaws.com/capacityType": "ON_DEMAND",
            "eks.amazonaws.com/nodegroup": "workers",
            "eks.amazonaws.com/nodegroup-image": "ami-0c89b104807c0b8c2",
            "eks.amazonaws.com/sourceLaunchTemplateId": "lt-09d1dabda97913944",
            "eks.amazonaws.com/sourceLaunchTemplateVersion": "1",
            "failure-domain.beta.kubernetes.io/region": "us-east-1",
            "failure-domain.beta.kubernetes.io/zone": "us-east-1a",
            "flux-operator": "true",
            "k8s.io/cloud-provider-aws": "6c22d656c63dd6b15e95a736e7429fb9",
            "kubernetes.io/arch": "arm64",
            "kubernetes.io/hostname": "ip-192-168-25-169.ec2.internal",
            "kubernetes.io/os": "linux",
            "node.kubernetes.io/instance-type": "hpc7g.16xlarge",
            "topology.kubernetes.io/region": "us-east-1",
            "topology.kubernetes.io/zone": "us-east-1a"
        },
        "name": "ip-192-168-25-169.ec2.internal",
        "resourceVersion": "7463",
        "uid": "7943a2cb-74a2-41cd-a26f-7b1af08c7a78"
    },
    "spec": {
        "providerID": "aws:///us-east-1a/i-02f3d2a816394602c"
    },
    "status": {
        "addresses": [
            {
                "address": "192.168.25.169",
                "type": "InternalIP"
            },
            {
                "address": "54.80.32.203",
                "type": "ExternalIP"
            },
            {
                "address": "ip-192-168-25-169.ec2.internal",
                "type": "InternalDNS"
            },
            {
                "address": "ip-192-168-25-169.ec2.internal",
                "type": "Hostname"
            },
            {
                "address": "ec2-54-80-32-203.compute-1.amazonaws.com",
                "type": "ExternalDNS"
            }
        ],
        "allocatable": {
            "cpu": "63770m",
            "ephemeral-storage": "76215832858",
            "hugepages-1Gi": "0",
            "hugepages-2Mi": "0",
            "hugepages-32Mi": "0",
            "hugepages-64Ki": "0",
            "memory": "126956280Ki",
            "pods": "198"
        },
        "capacity": {
            "cpu": "64",
            "ephemeral-storage": "83864556Ki",
            "hugepages-1Gi": "0",
            "hugepages-2Mi": "0",
            "hugepages-32Mi": "0",
            "hugepages-64Ki": "0",
            "memory": "129550072Ki",
            "pods": "198"
        },
        "conditions": [
            {
                "lastHeartbeatTime": "2023-07-28T17:36:53Z",
                "lastTransitionTime": "2023-07-28T17:08:48Z",
                "message": "kubelet has sufficient memory available",
                "reason": "KubeletHasSufficientMemory",
                "status": "False",
                "type": "MemoryPressure"
            },
            {
                "lastHeartbeatTime": "2023-07-28T17:36:53Z",
                "lastTransitionTime": "2023-07-28T17:08:48Z",
                "message": "kubelet has no disk pressure",
                "reason": "KubeletHasNoDiskPressure",
                "status": "False",
                "type": "DiskPressure"
            },
            {
                "lastHeartbeatTime": "2023-07-28T17:36:53Z",
                "lastTransitionTime": "2023-07-28T17:08:48Z",
                "message": "kubelet has sufficient PID available",
                "reason": "KubeletHasSufficientPID",
                "status": "False",
                "type": "PIDPressure"
            },
            {
                "lastHeartbeatTime": "2023-07-28T17:36:53Z",
                "lastTransitionTime": "2023-07-28T17:08:53Z",
                "message": "kubelet is posting ready status",
                "reason": "KubeletReady",
                "status": "True",
                "type": "Ready"
            }
        ],
        "daemonEndpoints": {
            "kubeletEndpoint": {
                "Port": 10250
            }
        },
        "images": [
            {
                "names": [
                    "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin@sha256:364d46e3e482f7cd03c586a69996348aa0ec8e6ff711d73013fbfba1ceb0b20d",
                    "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3"
                ],
                "sizeBytes": 168669831
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni-init:v1.13.2",
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni-init:v1.13.2-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni-init:v1.13.2",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni-init:v1.13.2-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/amazon-k8s-cni-init:v1.13.2"
                ],
                "sizeBytes": 56861009
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni:v1.13.2",
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni:v1.13.2-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni:v1.13.2",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni:v1.13.2-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/amazon-k8s-cni:v1.13.2"
                ],
                "sizeBytes": 42204731
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-west-2.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr.af-south-1.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2"
                ],
                "sizeBytes": 41111906
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/kube-proxy:v1.27.3-minimal",
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/kube-proxy:v1.27.3-minimal-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/kube-proxy:v1.27.3-minimal",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/kube-proxy:v1.27.3-minimal-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/eks/kube-proxy:v1.27.3-minimal"
                ],
                "sizeBytes": 28931949
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/kube-proxy:v1.27.1-minimal",
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/kube-proxy:v1.27.1-minimal-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/kube-proxy:v1.27.1-minimal",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/kube-proxy:v1.27.1-minimal-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/eks/kube-proxy:v1.27.1-minimal"
                ],
                "sizeBytes": 28931599
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-west-2.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr.af-south-1.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2"
                ],
                "sizeBytes": 21800423
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/pause:3.5",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/pause:3.5",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/eks/pause:3.5",
                    "602401143452.dkr.ecr-fips.us-west-2.amazonaws.com/eks/pause:3.5",
                    "602401143452.dkr.ecr.af-south-1.amazonaws.com/eks/pause:3.5"
                ],
                "sizeBytes": 250452
            }
        ],
        "nodeInfo": {
            "architecture": "arm64",
            "bootID": "6701d099-4393-4bef-8bd6-4b221908bf7e",
            "containerRuntimeVersion": "containerd://1.6.19",
            "kernelVersion": "5.10.184-175.731.amzn2.aarch64",
            "kubeProxyVersion": "v1.27.3-eks-a5565ad",
            "kubeletVersion": "v1.27.3-eks-a5565ad",
            "machineID": "ec25761e4d2afa2d3e7acfb35fc64463",
            "operatingSystem": "linux",
            "osImage": "Amazon Linux 2",
            "systemUUID": "ec25761e-4d2a-fa2d-3e7a-cfb35fc64463"
        }
    }
}

```

Note that the efa capacity and allocation are not present.
Here is output of a working node (note that they are present):

```bash
$ kubectl get node ip-192-168-0-161.ec2.internal -o json
```
```console
{
    "apiVersion": "v1",
    "kind": "Node",
    "metadata": {
        "annotations": {
            "alpha.kubernetes.io/provided-node-ip": "192.168.0.161",
            "node.alpha.kubernetes.io/ttl": "0",
            "volumes.kubernetes.io/controller-managed-attach-detach": "true"
        },
        "creationTimestamp": "2023-07-28T17:09:13Z",
        "labels": {
            "alpha.eksctl.io/cluster-name": "scaling-study-efa",
            "alpha.eksctl.io/nodegroup-name": "workers",
            "beta.kubernetes.io/arch": "arm64",
            "beta.kubernetes.io/instance-type": "hpc7g.16xlarge",
            "beta.kubernetes.io/os": "linux",
            "eks.amazonaws.com/capacityType": "ON_DEMAND",
            "eks.amazonaws.com/nodegroup": "workers",
            "eks.amazonaws.com/nodegroup-image": "ami-0c89b104807c0b8c2",
            "eks.amazonaws.com/sourceLaunchTemplateId": "lt-09d1dabda97913944",
            "eks.amazonaws.com/sourceLaunchTemplateVersion": "1",
            "failure-domain.beta.kubernetes.io/region": "us-east-1",
            "failure-domain.beta.kubernetes.io/zone": "us-east-1a",
            "flux-operator": "true",
            "k8s.io/cloud-provider-aws": "6c22d656c63dd6b15e95a736e7429fb9",
            "kubernetes.io/arch": "arm64",
            "kubernetes.io/hostname": "ip-192-168-0-161.ec2.internal",
            "kubernetes.io/os": "linux",
            "node.kubernetes.io/instance-type": "hpc7g.16xlarge",
            "topology.kubernetes.io/region": "us-east-1",
            "topology.kubernetes.io/zone": "us-east-1a"
        },
        "name": "ip-192-168-0-161.ec2.internal",
        "resourceVersion": "7448",
        "uid": "34c2c395-91e8-436e-ad69-4e78789ad461"
    },
    "spec": {
        "providerID": "aws:///us-east-1a/i-0314458f8b2c41e36"
    },
    "status": {
        "addresses": [
            {
                "address": "192.168.0.161",
                "type": "InternalIP"
            },
            {
                "address": "54.81.95.18",
                "type": "ExternalIP"
            },
            {
                "address": "ip-192-168-0-161.ec2.internal",
                "type": "InternalDNS"
            },
            {
                "address": "ip-192-168-0-161.ec2.internal",
                "type": "Hostname"
            },
            {
                "address": "ec2-54-81-95-18.compute-1.amazonaws.com",
                "type": "ExternalDNS"
            }
        ],
        "allocatable": {
            "cpu": "63770m",
            "ephemeral-storage": "76215832858",
            "hugepages-1Gi": "0",
            "hugepages-2Mi": "14082Mi",
            "hugepages-32Mi": "0",
            "hugepages-64Ki": "0",
            "memory": "112536312Ki",
            "pods": "198",
            "vpc.amazonaws.com/efa": "1"
        },
        "capacity": {
            "cpu": "64",
            "ephemeral-storage": "83864556Ki",
            "hugepages-1Gi": "0",
            "hugepages-2Mi": "14082Mi",
            "hugepages-32Mi": "0",
            "hugepages-64Ki": "0",
            "memory": "129550072Ki",
            "pods": "198",
            "vpc.amazonaws.com/efa": "1"
        },
        "conditions": [
            {
                "lastHeartbeatTime": "2023-07-28T17:36:48Z",
                "lastTransitionTime": "2023-07-28T17:09:13Z",
                "message": "kubelet has sufficient memory available",
                "reason": "KubeletHasSufficientMemory",
                "status": "False",
                "type": "MemoryPressure"
            },
            {
                "lastHeartbeatTime": "2023-07-28T17:36:48Z",
                "lastTransitionTime": "2023-07-28T17:09:13Z",
                "message": "kubelet has no disk pressure",
                "reason": "KubeletHasNoDiskPressure",
                "status": "False",
                "type": "DiskPressure"
            },
            {
                "lastHeartbeatTime": "2023-07-28T17:36:48Z",
                "lastTransitionTime": "2023-07-28T17:09:13Z",
                "message": "kubelet has sufficient PID available",
                "reason": "KubeletHasSufficientPID",
                "status": "False",
                "type": "PIDPressure"
            },
            {
                "lastHeartbeatTime": "2023-07-28T17:36:48Z",
                "lastTransitionTime": "2023-07-28T17:09:17Z",
                "message": "kubelet is posting ready status",
                "reason": "KubeletReady",
                "status": "True",
                "type": "Ready"
            }
        ],
        "daemonEndpoints": {
            "kubeletEndpoint": {
                "Port": 10250
            }
        },
        "images": [
            {
                "names": [
                    "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin@sha256:364d46e3e482f7cd03c586a69996348aa0ec8e6ff711d73013fbfba1ceb0b20d",
                    "602401143452.dkr.ecr.us-east-1.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3"
                ],
                "sizeBytes": 168669831
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni-init:v1.13.2",
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni-init:v1.13.2-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni-init:v1.13.2",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni-init:v1.13.2-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/amazon-k8s-cni-init:v1.13.2"
                ],
                "sizeBytes": 56861009
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni:v1.13.2",
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni:v1.13.2-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni:v1.13.2",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni:v1.13.2-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/amazon-k8s-cni:v1.13.2"
                ],
                "sizeBytes": 42204731
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-west-2.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr.af-south-1.amazonaws.com/amazon-k8s-cni:v1.12.6-eksbuild.2"
                ],
                "sizeBytes": 41111906
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/kube-proxy:v1.27.3-minimal",
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/kube-proxy:v1.27.3-minimal-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/kube-proxy:v1.27.3-minimal",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/kube-proxy:v1.27.3-minimal-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/eks/kube-proxy:v1.27.3-minimal"
                ],
                "sizeBytes": 28931949
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/kube-proxy:v1.27.1-minimal",
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/kube-proxy:v1.27.1-minimal-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/kube-proxy:v1.27.1-minimal",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/kube-proxy:v1.27.1-minimal-eksbuild.1",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/eks/kube-proxy:v1.27.1-minimal"
                ],
                "sizeBytes": 28931599
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr-fips.us-west-2.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2",
                    "602401143452.dkr.ecr.af-south-1.amazonaws.com/amazon-k8s-cni-init:v1.12.6-eksbuild.2"
                ],
                "sizeBytes": 21800423
            },
            {
                "names": [
                    "602401143452.dkr.ecr-fips.us-east-1.amazonaws.com/eks/pause:3.5",
                    "602401143452.dkr.ecr-fips.us-east-2.amazonaws.com/eks/pause:3.5",
                    "602401143452.dkr.ecr-fips.us-west-1.amazonaws.com/eks/pause:3.5",
                    "602401143452.dkr.ecr-fips.us-west-2.amazonaws.com/eks/pause:3.5",
                    "602401143452.dkr.ecr.af-south-1.amazonaws.com/eks/pause:3.5"
                ],
                "sizeBytes": 250452
            }
        ],
        "nodeInfo": {
            "architecture": "arm64",
            "bootID": "0bc33554-8274-4a37-a2a2-d17d4adde48f",
            "containerRuntimeVersion": "containerd://1.6.19",
            "kernelVersion": "5.10.184-175.731.amzn2.aarch64",
            "kubeProxyVersion": "v1.27.3-eks-a5565ad",
            "kubeletVersion": "v1.27.3-eks-a5565ad",
            "machineID": "ec2748d9b323ee9b93cc31c76e43c115",
            "operatingSystem": "linux",
            "osImage": "Amazon Linux 2",
            "systemUUID": "ec2748d9-b323-ee9b-93cc-31c76e43c115"
        }
    }
}
```
### First Email Requests

Here are requests from the first email (without the list) and some comments.

> My understanding to the issue from the most recent explanation provided by yourself is that, it could not be linked to the eksctl version since it is provisioning the cluster and the other resources correctly and just the EFA device daemonsets are failing to work as expected, making the devices inaccessible. 

I do not agree with this statement - we are using the exact same eksctl binary that has worked many times before. We do not believe it is related to an eksctl version, since this factor has been constant. It also doesn't make sense given that some nodes are working and some not (created with the same logic / binary). We believe there is something erroneous happening with AWS services that we are not privy to, especially since these are relatively new nodes.

> 1. Please share the steps and any config files related to the provisioning (if you can).

The eksctl config is shared above in the [cluster config](#cluster-config) section. As previously stated, this exact config has worked many times before.

> 2. Please share the error information from the daemonsets (which are failing). You can do kubectl logs <pod name> -n <namespace> for the pods controlled by that daemonset which is failing. OR if the daemonset is created in a particular namespace other than Kube-system, you can get all the events from that namespace by executing kubectl get events -n <namespace>. Please also execute kubectl describe ds <daemonset name>

We have provided this output in [command output](#command-output).

### Clean Up

To clean up I did:

```bash
$ ./bin/eksctl delete cluster -f ./config/eks-config.yaml 
```

And here is complete output:

```console
$ ./bin/eksctl delete cluster -f ./config/eks-config.yaml 
```
```bash
2023-07-28 12:00:38 [ℹ]  deleting EKS cluster "scaling-study-efa"
2023-07-28 12:00:38 [ℹ]  will drain 0 unmanaged nodegroup(s) in cluster "scaling-study-efa"
2023-07-28 12:00:38 [ℹ]  starting parallel draining, max in-flight of 1
2023-07-28 12:00:39 [ℹ]  cordon node "ip-192-168-0-161.ec2.internal"
2023-07-28 12:00:39 [ℹ]  cordon node "ip-192-168-2-130.ec2.internal"
2023-07-28 12:00:39 [ℹ]  cordon node "ip-192-168-2-48.ec2.internal"
2023-07-28 12:00:39 [ℹ]  cordon node "ip-192-168-23-9.ec2.internal"
2023-07-28 12:00:39 [ℹ]  cordon node "ip-192-168-25-136.ec2.internal"
2023-07-28 12:00:39 [ℹ]  cordon node "ip-192-168-25-169.ec2.internal"
2023-07-28 12:00:39 [ℹ]  cordon node "ip-192-168-27-250.ec2.internal"
2023-07-28 12:00:39 [ℹ]  cordon node "ip-192-168-31-107.ec2.internal"
2023-07-28 12:00:52 [✔]  drained all nodes: [ip-192-168-2-48.ec2.internal ip-192-168-0-161.ec2.internal ip-192-168-23-9.ec2.internal ip-192-168-31-107.ec2.internal ip-192-168-27-250.ec2.internal ip-192-168-2-130.ec2.internal ip-192-168-25-136.ec2.internal ip-192-168-25-169.ec2.internal]
2023-07-28 12:00:53 [ℹ]  deleted 0 Fargate profile(s)
2023-07-28 12:00:54 [✔]  kubeconfig has been updated
2023-07-28 12:00:54 [ℹ]  cleaning up AWS load balancers created by Kubernetes objects of Kind Service or Ingress
2023-07-28 12:00:55 [ℹ]  
2 sequential tasks: { delete nodegroup "workers", delete cluster control plane "scaling-study-efa" [async] 
}
2023-07-28 12:00:55 [ℹ]  will delete stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 12:00:55 [ℹ]  waiting for stack "eksctl-scaling-study-efa-nodegroup-workers" to get deleted
2023-07-28 12:00:55 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 12:01:26 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 12:02:01 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 12:03:43 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 12:05:24 [ℹ]  waiting for CloudFormation stack "eksctl-scaling-study-efa-nodegroup-workers"
2023-07-28 12:05:24 [ℹ]  will delete stack "eksctl-scaling-study-efa-cluster"
2023-07-28 12:05:25 [✔]  all cluster resources were deleted
```

