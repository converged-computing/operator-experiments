# Compute Engine Experiments

This repo contains scripts and Terraform configs that make it easy to deploy the 
[Flux Framework](https://flux-framework.org/) resource job management software designed
by LLNL engineers in the Google Cloud Platform. Specifically, we will do a deployment
that connects to Google Cloud Storage. The steps you should take are documented in:

 1. [build-images](./build-images/) needed for compute and login nodes using Cloud Builder
 1. [experiments](./experiments) apply terraform configs to create the entire setup, and run experiments.
 
## Experiment Setup

The following things we will want to do for each experiment:

 - ensure that we have enough quota for instances, etc.
 - do a cost estimation based on instance usage, storage, and time
 
## Comparison

- Flux nodes: Flux operator requires a container rebuild, identical, Compute Engine requires a VM rebuild (multiple)
- Interaction: Flux operator affords more programmatic interactions (Compute Engine requires a login)
-   
