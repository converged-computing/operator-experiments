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

# Run example with these parameters
$ python run-job.py ${project_id} --cpu-milli 1000 --memory 1000 --tasks ${tasks} --max-run-duration 3600s --bucket ${bucket} --job-name hello-world-mpi-001

```

Note that the above uses a lot of defaults!

