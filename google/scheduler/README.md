# Fluence Scheduler

Here we want to compare the Kubernetes Default Scheduler with [Fluence](https://github.com/flux-framework/flux-k8s).

## Testing

 - [run0](run0): basic testing for setup (very small scale)
 - [run1](run1): fluence scheduler is unblocked, testing canopie22 (Illegal instruction core dumped)
 - [run2](run2): Prototyping using the Flux Operator (basics)
 - [run3](run3): With fluence + the flux operator working, try emulating the logic of the original canopie 22 experiments with multiple sizes of lammps.
 - [run4](run4): with experiments prototyped and fluence fixes merged, reproduce fluence bug and look into.
 - [run5](run5): is testing an updated branch of fluence
 - [run6-min-size](run6-min-size) testing updated fluence / default scheduler at smaller sizes
 - [run7-timestamp](run7-timestamp) aims to test using millisecond timestamps (still looking for interleaving)
 - [run8](run8): first attempt to run with kueue, cocsheduling, default, and fluence
 - [run9](run9): updating to use simple [job](https://kubernetes.io/docs/tasks/job/job-with-pod-to-pod-communication/) instead of MiniCluster, this was primarily debugging (with several clusters) to get things working.
 - [run10](run10): this was the single experiment of the above.
