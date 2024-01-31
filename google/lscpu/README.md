# lscpu

Let's run the simplest of jobs, across instance types, to run lscpu (and maybe lstopo)?

## Dependencies

First, create the virtual environment:

```bash
python -m venv env
source env/bin/activate
pip install google-cloud-batch google-cloud-storage jinja2
```

Note that you will need to be authenticated to Google Cloud `google cloud auth`
and have the Batch API enabled.

## Setup

We will need to upload assets to a private bucket. Here is what that looks like:

```bash
project_id="$(gcloud config get-value core/project)"
bucket="lscpu-experiment-bucket"

# Create the bucket
gcloud storage buckets create gs://${bucket}
```

We will do this just once and then save to our Google Cloud storage to reuse.

## Run Job

Since we want to automate (and minimize YAML and json files) we represent our workflow
in Python.

```bash
# Get google project id, bucket name (should already exist with netmark code)
project_id="$(gcloud config get-value core/project)"

# Note we are using defaults for most arguments here
python run-job.py ${project_id} --machine-type c2-standard-4 --job-name lscpu-job-001
```

I'm going to generate a list (and tweak it to small sizes):

```
gcloud compute machine-types list --filter="zone:(us-central1)" --uri > machines.txt 
```
```
for machine in $(cat machines.txt); do
   echo $machine
   python run-job.py ${project_id} --machine-type $machine --job-name lscpu-$machine-001
done
```

NOTE that Batch's definition of a "task" is one scoped piece of work, and is NOT an MPI task. This is not relevant here since we aren't running MPI, but for the future (this was a point of confusion for me) remember:

 - tasks per node is the number of scoped work pieces we want running per google instance (regardless of cores)
 - parallelism is the number of instances (nodes) to run
 - we can use barriers only if parallelism == tasks
 
To download:

```bash
gsutil -m cp -r "gs://lscpu-experiment-bucket/lscpu" .
```

You can see results in [lscpu](lscpu)
