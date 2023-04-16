# Bare Metal Comparison

> How does the Flux Operator compare to running on "bare metal" GCP instances?

This experiment will have a few parts - first learning about [how Flux is setup in GCP](https://github.com/GoogleCloudPlatform/scientific-computing-examples/tree/main/fluxfw-gcp) and then tweaking this setup to be comparable to the Flux Operator and designing an experiment around it.
This directory contains three components:

 - [compute-engine](compute-engine): experiments for compute engine.
 - **flux-operator**: equivalent experiments with the Flux operator (TBA)

For both sets of experiments, you should then login to your Google Cloud account, typically with `gcloud auth login`
and then `gcloud config set project <myproject>`. Then proceed to the experiment subfolder
of your choice.
