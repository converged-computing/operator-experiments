# Indexed Job Times

We are interested to understand how creating batches of pods varies from creating a single indexed job.
I'm going to do some basic tests (first locally) to test that.

## Setup

Create a kind cluster

```bash
kind create cluster
```

And then run a particular experiment:

```bash
python pod-events.py experiments/size-4 --size 4
```
