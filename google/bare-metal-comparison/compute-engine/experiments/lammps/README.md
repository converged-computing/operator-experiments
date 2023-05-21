# Flux Framework LAMMPS Cluster Deployment

These experiments were attempting to compare a run of LAMMPS on the Flux Operator
vs. Compute Engine.

 - [run1](run1): we had issue with scaling Compute Engine > 10 compute nodes with compact, and networking never took for most cluster sizes above that.
 - [run2](run2): we wanted to try again with the c2 instance type to rule that out.
