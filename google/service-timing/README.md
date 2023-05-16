# Service Timing Experiments

We discovered slow networking on [GKE and reported the issue](https://github.com/kubernetes/kubernetes/issues/117819) and these series
of experiments are attempting to investigate different aspects.

 - [run1](run1) was my original testing done on GKE to report the issue (May 4, 2023)
 - [run2](run2) was a secondary test to run nslookup across different cluster flags (May 16, 2023)
