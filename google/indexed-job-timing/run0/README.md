# Indexed Job Times

We are interested to understand how creating batches of pods varies from creating a single indexed job.
I'm going to do some basic tests (first locally) to test that.

## Setup

### 1. Create Cluster

Create a kind cluster

```bash
kind create cluster
```

### 2. Create Experiments

We have templates and a script to generate the files!

```bash
python generate-size.py 8
python generate-size.py 16
python generate-size.py 32
python generate-size.py 64
```

### 3. Run Experiment

And then run a particular experiment, some number of times:

```bash
# 4 pods
for i in {0..20}; do
  echo "Running experiment ${i} for size-4 test"
  python pod-events.py experiments/size-4 --size 4 --idx=${i}
done

# 8 pods
for i in {0..20}; do
  echo "Running experiment ${i} for size-8 test"
  python pod-events.py experiments/size-8 --size 8 --idx=${i}
done

# 16 pods
for i in {0..20}; do
  echo "Running experiment ${i} for size-16 test"
  python pod-events.py experiments/size-16 --size 16 --idx=${i}
done

# 32 pods
for i in {0..20}; do
  echo "Running experiment ${i} for size-32 test"
  python pod-events.py experiments/size-32 --size 32 --idx=${i}
done

# Lol, hope this is OK for my computer...
# 64 pods
for i in {0..20}; do
  echo "Running experiment ${i} for size-64 test"
  python pod-events.py experiments/size-64 --size 64 --idx=${i}
done
```

What isn't clear is if the actual timing of pods will get in the way...

### 4. Process Result Data

```bash
python analyze-results.py data/
```

### 5. View Results

Here is an overview of times:

I'm wondering how the watch loop influences the "all" create times? And if there are any other issues in the experiment running design.
See my notes below.

#### ContainersReady

![img/times-experiment-containersready_times-experiments-containersready.png](img/times-experiment-containersready_times-experiments-containersready.png)

#### Initialized

![img/times-experiment-initialized_times-experiments-initialized.png](img/times-experiment-initialized_times-experiments-initialized.png)

#### PodScheduled

![img/times-experiment-podscheduled_times-experiments-podscheduled.png](img/times-experiment-podscheduled_times-experiments-podscheduled.png)

#### Ready

![img/times-experiment-ready_times-experiments-ready.png](img/times-experiment-ready_times-experiments-ready.png)

#### Create Times (all)

![img/times-experiment-watch_create_times-experiments-watch_create.png](img/times-experiment-watch_create_times-experiments-watch_create.png)

#### Delete Times (all)

![img/times-experiment-watch_delete_times-experiments-watch_delete.png](img/times-experiment-watch_delete_times-experiments-watch_delete.png)


### 6. Observations

First note that this is running locally, and the main goal was to design an experiment that looks at single pod vs. indexed job creation times. 
In summary, we have an experiment that will create pods or an indexed job 20 times across a range of sizes (4 to 64 here).
Observations:

- PodScheduled and Initialized correspond exactly with the creationTime. I also checked that creationTime does not change between events. So I'm not sure these two events are meaningful.
- ContainersReady and Ready don't seem significantly different, but would be interesting to see how they scale.
- watch_create does have some tiny differences - and I want to make sure this isn't an artifact of the experiment. What I do for each of apply and delete is have all the pods (or single indexed job) in a yaml file (so they are all applied "at the same time" as best I could) and then I immediately start watching and time that function. It appears that for indexed job that function timed wrapper is faster. But if the Ready/ContainersReady and other times are comparable, I'm wondering where that different is coming from. See the top level README for how I decide that a container is created (and we exit out of that watch loop)
- the same for watch_delete is interesting, and I want to see how that scales. This was interesting to measure because by default, kubecl hangs. I added & to make sure it doesn't and then (again) immediately start watching. It does seem to jump up at 64 pods.

I am looking for feedback on:

- my design (what I'm measuring, how I'm doing it, what I might do differently)
- what number of nodes / sizes we should test on a "real" cluster (aka cloud)

I'm going to anticipate not getting feedback and do some quick research on how many pods a node can support, and then try to stress that on a relatively inexpensive cloud cluster size. This "actual data" will be more meaningful for discussion I think.
