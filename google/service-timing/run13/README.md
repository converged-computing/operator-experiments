# Service Timing

For these experiments I'm going to test random network flags. For each experiment, see the corresponding READMEs.
I've adjusted the timeouts to be half (e.g., 2,4,6,...10, None instead of 1..10,None and only 5 iterations per period.

## 1. Local Cache 

I found something called [LocalCache](https://cloud.google.com/kubernetes-engine/docs/best-practices/networking) that would
cache the DNS query lookups. If the issue is related to this, we could see improvement.

 - [e2-medium-8-local-cache](e2-medium-8-local-cache) a first shot test (to see if the cluster would even come up!)
 - [c2-standard-8-8-local-cache](c2-standard-8-8-local-cache) adding the correct threading / compact mode.
 - [c2d-standard-112-64](c2d-standard-112-64) attempting to run an actual large cluster with chonker machines with LAMMPS

## Current Conclusions

- The `--addons=NodeLocalDNS` to create a local DNS cache via a daemonset seems to get around the creation issues.
- The pattern with/without a service reverses with this flag - adding the service is slower (as I would have expected)!
- Testing this flag with a larger cluster, I'm able to create a relatively large one (size 64) for the first time!
- The LAMMPS run across sizes actually _works_ albeit it's slow
  
From the first three points, I think the service timing issue (that warranted these experiments) is related to DNS.
We can (for the time being) get around it dually with setting the zeromq timeout (to avoid the exponential backoff, which
we already figured out) and using this daemonset to cache DNS.

From the last experiment, we are seeing the switch between connecting cost and contribution of node size (cpu for LAMMPS that should make it faster).
I think we can conclude with the current GCP networking, if one wants to run experiments, it's better to use a few number of really large nodes to avoid this networking cost.

## Others

Other ideas to try in the future:

 - [NCCL Fast Socket](https://cloud.google.com/kubernetes-engine/docs/how-to/nccl-fast-socket) if we can use GPU
 - [ICI](https://www.semianalysis.com/p/google-ai-infrastructure-supremacy) seems to be a networking stack for TPUs?
 
>  One of Google’s biggest innovations in its AI infrastructure is the use of a custom networking stack between TPUs, ICI. This link is low latency and high performance relative to costly Ethernet and InfiniBand deployments. It is more analogous to Nvidia’s NVLink.

 - We had luck using ARM instances (Graviton) on AWS, so I thought it might make sense to give a shot here.
[Here is an example article](https://engineering.sada.com/working-with-arm64-machines-on-google-kubernetes-engine-8667984c566e).
 - [gvnic](https://cloud.google.com/sdk/gcloud/reference/container/clusters/create) (see flag there) I think I was using this wrong - it needs to be added via a node group.
