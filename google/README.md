# Flux Operator Experiments

> On Google Cloud! ☁️

The goal of these experiments is to test the Flux Operator at small scales, meaning
taking simple workflows and comparing execution between using the [Flux Operator](https://github.com/flux-framework/flux-operator)
and [a more native approach](https://github.com/GoogleCloudPlatform/scientific-computing-examples/tree/main/fluxfw-gcp).

 - [lammps](lammps)
 - [osu-benchmarks](osu-benchmarks)
 - [resources](resources): getting more than one flux pod per node working!
 - [indexed-job-timing](indexed-job-timing): comparison of pods a la-carte vs with indexed jobs.
 - [autoscale](autoscale): early autoscaling work
 - [bare-metal-comparison](bare-metal-comparison): attempted start to compare GKE to CE, never went far because we couldn't get compact on CE, and lammps to run on GKE.
 - [networking](networking) and [service-timing](service-timing): testing a networking bug with a service
 - [rootless-kubernetes](rootless-kubernetes)
 - [scheduler](scheduler): testing fluence against the default scheduler
 - [workflows](workflows)
 
For all of these examples, you will need a [Google Cloud Project](https://console.cloud.google.com) and to enable the Kubernetes Engine API.
If you are running these are your personal cloud account, it's recommended to use
the [pricing calculator](https://cloud.google.com/products/calculator) before creating any resources!


