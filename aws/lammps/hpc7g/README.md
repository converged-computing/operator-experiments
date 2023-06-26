# Testing HPC7G

Here we are going to test a small setup on AWS that uses this new instance type!
You can read more about the [announcement here](https://aws.amazon.com/blogs/aws/new-amazon-ec2-hpc7g-instances-powered-by-aws-graviton3e-processors-optimized-for-high-performance-computing-workloads/). The idea will be that if we like this setup, we can do more scaled
experiments (also testing JobSet with HyperQueue and HTCondor and slurm, if ready).
For now we will just run the small experiment with the Flux Operator.
We can't easily compare two clusters with different nodes, but there isn't much
to do about that :)

 - [run1](run1): a small set of tests to ensure that everything still works!


See [efa-arm.md](efa-arm.md) for building a custom image for the EFA adapted with ARM.
I'm still not sure how this works - likely we are missing some entrypoint but I haven't tried
it yet. 
 
## Latency

This is from [@milroy](https://github.com/milroy) to compare hpc6a vs hpc7g latency

> the CPU utilization on hpc7g is also much lower (consistent with higher latency communication):

```console
Performance: 0.012 ns/day, 2058.199 hours/ns, 1.350 timesteps/s
79.7% CPU use with 768 MPI tasks x 1 OpenMP threads
```
vs hpc6a:

```console
Performance: 0.010 ns/day, 2476.087 hours/ns, 1.122 timesteps/s
97.8% CPU use with 768 MPI tasks x 1 OpenMP threads
```

