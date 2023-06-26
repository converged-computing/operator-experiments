# Testing HPC7G

Here we are going to test a small setup on AWS that uses this new instance type!
You can read more about the [announcement here](https://aws.amazon.com/blogs/aws/new-amazon-ec2-hpc7g-instances-powered-by-aws-graviton3e-processors-optimized-for-high-performance-computing-workloads/). The idea will be that if we like this setup, we can do more scaled
experiments (also testing JobSet with HyperQueue and HTCondor and slurm, if ready).
For now we will just run the small experiment with the Flux Operator.
We can't easily compare two clusters with different nodes, but there isn't much
to do about that :)

 - [run1](run1): a small set of tests to ensure that everything still works!
