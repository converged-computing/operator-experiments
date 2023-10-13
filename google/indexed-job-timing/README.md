# Indexed Job Timing

I'm curious to see how it compares to create / delete an indexed job vs.
regular pods.

- [run0](run0): Local testing / setup using kind.


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
