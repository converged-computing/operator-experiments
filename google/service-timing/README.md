# Service Timing Experiments

We discovered slow networking on [GKE and reported the issue](https://github.com/kubernetes/kubernetes/issues/117819) and these series
of experiments are attempting to investigate different aspects.

 - [run1](run1) was my original testing done on GKE to report the issue (May 4, 2023)
 - [run2](run2) was a secondary test to run nslookup across different cluster flags (May 16, 2023)
 - [run3](run3) ran telnet in the worker pod to look at connection times/patterns to the broker leader (index 0)
 - [run4](run4) used a test deployment of the operator that wrapped flux start with strace
 - [run5](run5) attempts to remove DNS by getting pod ip addresses and writing them into `/etc/hosts`
 - [run6](run6) is an effort to put together best practices of what we learned and reproduce the run1 experiments with improvements (May 17, 2023)
 - [run7](run7) the same but adding back the coredns to see if it replicates the original error
 - [run8](run8) was one more attempt to reproduce the issue (done, and one huge timeout)
 - [run9](run9) was the final case to replicate (did)
 - [run10](run10) is the equivalent experiment but scaled up to a larger cluster
 - [run11](run11) are results from Dmitri on the Google networking team.
