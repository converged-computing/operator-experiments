# Sole Tenant Nodes

We learned from [run13](run13) that adding a local node cache for DNS helps to bring up the cluster. Now
we are going to try adding on [tier-1 networking](https://cloud.google.com/kubernetes-engine/docs/how-to/using-tier-1) 
and using [sole tenant nodes](https://cloud.google.com/kubernetes-engine/docs/how-to/sole-tenancy) first on the OSU benchmarks
to see how it performs. We can then take the best result and translate this over to the original LAMMPS runs.
We are starting with the OSU benchmarks because they only require 2 nodes.

## 1. Create Node Templates

See sole-tenant nodes available. I was interested in c2 and c3 in central:

```bash
$ gcloud compute sole-tenancy node-types list|grep c3 | grep central
c3-node-176-1408   us-central1-a              176   1441792
c3-node-176-352    us-central1-a              176   360448
c3-node-176-704    us-central1-a              176   720896
c3-node-176-1408   us-central1-b              176   1441792
c3-node-176-352    us-central1-b              176   360448
c3-node-176-704    us-central1-b              176   720896
c3-node-176-1408   us-central1-c              176   1441792
c3-node-176-352    us-central1-c              176   360448
c3-node-176-704    us-central1-c              176   720896
c3-node-176-352    us-central1-d              176   360448

$ gcloud compute sole-tenancy node-types list|grep c2 | grep central
c2-node-60-240     us-central1-a              60    245760
c2-node-60-240     us-central1-b              60    245760
c2-node-60-240     us-central1-c              60    245760
c2-node-60-240     us-central1-f              60    245760
```

Probably we will start with c2 since they are cheaper, and then try c3. Specifically I want to try:

- c2-node-60-240
- c3-node-176-352

Since those are the smallest. See each corresponding directory for full instructions.

 - [c2-node-60-240](c2-node-60-240)
 
Not done yet:

```bash
# For the c3 instance type
gcloud compute sole-tenancy node-templates create sole-tenant-c3-node-176-352 \
    --node-type=c3-node-176-352 \
    --region=us-central1
```
