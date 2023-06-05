# Hello World MPI

This is a "hello world" example of MPI.

## Dependencies

First, create the virtual environment:

```bash
python -m venv env
source env/bin/activate
pip install google-cloud-batch
```

Note that you will need to be authenticated to Google Cloud `google cloud auth`
and have the Batch API enabled.

## Run Job

Since we want to automate (and minimize YAML and json files) we represent our workflow
in Python.

```bash
# Get google project id, bucket name (should already exist with netmark code)
project_id="$(gcloud config get-value core/project)"
bucket=netmark-experiment-bucket
tasks=4

# Run example with these parameters
$ python run-job.py ${project_id} --cpu-milli 1000 --memory 1000 --tasks ${tasks} --max-run-duration 3600s --bucket ${bucket} --job-name hello-world-mpi-041
```

Note that the above uses a lot of defaults! Importantly, we need to source the vars.sh in the setup script - the 
logs will erroneously show you the source, but it's just doing an echo to show you how you would do it.
When the examples are working, you should see:

```
Hello, world, I am 3 of 4, (Intel(R) MPI Library 2021.8 for Linux* OS , 42)
Hello, world, I am 1 of 4, (Intel(R) MPI Library 2021.8 for Linux* OS , 42)
Hello, world, I am 2 of 4, (Intel(R) MPI Library 2021.8 for Linux* OS , 42)
Hello, world, I am 0 of 4, (Intel(R) MPI Library 2021.8 for Linux* OS , 42) 
```
in the logs.
