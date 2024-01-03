# Fluence Scheduler

Here we want to compare the Kubernetes Default Scheduler with [Fluence](https://github.com/flux-framework/flux-k8s).

## Testing

 - [run0](run0): basic testing for setup (very small scale)
 - [run1](run1): fluence scheduler is unblocked, testing canopie22 (Illegal instruction core dumped)
 - [run3](run3): With fluence + the flux operator working, try emulating the logic of the original canopie 22 experiments with multiple sizes of lammps.
