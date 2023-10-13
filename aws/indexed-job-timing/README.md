# Indexed Job Timing

This is a continuation of [early testing](../../google/indexed-job-timing) to look at indexed jobs vs pods. Instead
of running locally with kind, here we will run on an actual cluster.

- [run0](run0): testing on 1 x m5.16xlarge instances to see how many pods it actually allows, and total time it takes.
- [run1](run1): testing on N x m5.16xlarge instances to try to scale up to 1k pods.

I am reproducing the documentation there here so it is clear about the strategy for assessing times. If there is a flaw here
the experiments and data are not useful.

## Timing Strategy

Creation and deletion are not determined by the apply of yaml, but rather we apply and don’t wait, and then immediately start the watch function. The watch function for create or delete encompasses the total time from start until a final indicator of creation or deletion. We can also derive the creation time for a pod directly from the event object saved for each one.

Conditions for being done watching include:

  - **create** this is True for all 4 statuses (see example below)
  - **delete** Seeing all individual pods have event type DELETED.

Here is an example of a pod that is done creation. Note the presence of 4 conditions that are all true:

```json
"status": {
"phase": "Running",
"conditions": [
   {
       "type": "Initialized",
       "status": "True",
       "lastProbeTime": null,
       "lastTransitionTime": "2023-10-13T08:05:44Z"
   },
   {
       "type": "Ready",
       "status": "True",
       "lastProbeTime": null,
       "lastTransitionTime": "2023-10-13T08:05:46Z"
   },
   {
        "type": "ContainersReady",
        "status": "True",
        "lastProbeTime": null,
        "lastTransitionTime": "2023-10-13T08:05:46Z"
   },
   {
        "type": "PodScheduled",
        "status": "True",
        "lastProbeTime": null,
        "lastTransitionTime": "2023-10-13T08:05:44Z"
    }
],
```

Note that `lastTransitionTime` is:

> Timestamp for when the Pod last transitioned from one status to another.

Definitions can be found [here](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/). We may likely want to find other strategies for getting times - this is just a first shot. Also note that We can’t wait for the yaml to apply because it doesn’t hang much with create but hangs almost for the entirely of delete and we want to measure them equally.

## Things to Look at

- First creation with container pulls vs not (not done yet, requires deleting cluster each time)
- Creation times for each over time (this is what we are currently looking at)
- Overall variability 
- Time to go from False to True for each status
