# Netmark

Here we want to test doing Netmark runs with Google Batch.

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

Since Netmark is private, to build it in batch we require that you have access to the private repository
to clone, and you are then able to upload assets to a private bucket. Here is what that looks like:

```bash
project_id="$(gcloud config get-value core/project)"
bucket="netmark-experiment-bucket"

# Create the bucket
gcloud storage buckets create gs://${bucket}

# Clone netmark and copy it there, removing history, etc.
git clone --depth 1 git@github.com:ggeorgakoudis/netmark

# Add this import to netmark.c
# #include <getopt.h>
rm -rf netmark/.git
gcloud storage cp --recursive ./netmark/* gs://${bucket}/netmark
```


Google must have some secret deal with Intel to use their compilers, because
(aside from the others not working well) they don't actually provide mpicc to compile
anything. So we need to provide it ourselves, and we will follow [this example](https://github.com/GoogleCloudPlatform/batch-samples/tree/d026683aa27d01111ec68a66d07abadab1712730/wrf)
to prepare a spack environment. You'll do this locally on your machine.

```
git clone -c feature.manyFiles=true --depth 1 https://github.com/spack/spack.git
. spack/share/spack/setup-env.sh
spack mirror add gcs https://storage.googleapis.com/pnnl-clouddays22-workshop
spack buildcache keys --install --trust
# I didn't run these :)
# spack install gcc@8.2.0
# spack load gcc@8.2.0
# spack compiler find
spack install intel-mpi@2018.4.274
spack load intel-mpi@2018.4.274
cd netmark
make
```

Finally, upload netmark.x to your same storage.

```bash
project_id="$(gcloud config get-value core/project)"
bucket="netmark-experiment-bucket"
gcloud storage cp ./netmark.x gs://${bucket}/netmark/netmark.x
```


We will do this just once and then save to our Google Cloud storage to reuse.

Now we have the code in the cloud (privately) and can continue to run out workflow!

## Run Job

Since we want to automate (and minimize YAML and json files) we represent our workflow
in Python.

```bash
# Get google project id, bucket name (should already exist with netmark code)
project_id="$(gcloud config get-value core/project)"
bucket="netmark-experiment-bucket"
tasks=4

# Run netmark with these parameters
$ python run-job.py ${project_id} --cpu-milli 1000 --memory 1000 --tasks ${tasks} --max-run-duration 3600s --bucket ${bucket} --machine-type c2-standard-16 --job-name netmark-job-001
```

Note that I think for machine type, if we expect 8 cores, we actually need a -16 instance type since there are 2vcpu per actual.
Also note that the above isn't working, but someone that likes MPI can debug!

```
textPayload: "[netmark-job-010-7076dba4-bda2-4045-a00-group0-0-fqhr:12658] [[INVALID],INVALID] FORCE-TERMINATE AT Not found:-13 - error ../../../../../../orte/mca/plm/rsh/plm_rsh_component.c(335)
```

## Feedback for Google Batch

- For MPI workloads in a container, it would be nice to have Singularity support and some means to bind MPI libraries to container
- The "hello world" example (with hostname) doesn't use MPI, would be good to have an actual MPI example
- Really nice UI for seeing everything! I couldn't easy find logging, however. That might be front and center!
- Going from scheduled to running seems a bit slow
- The logging is pretty hard to follow, especially with multiple workers running - it looks like Cloud Build and I wish it was just a big block of text to read!
- Debugging is hard - would be nice to have an interactive job
- It would be nice to have it more automated to be able to submit a job with the same name (and after the next number added)
- It's borderline monster to name your bin "bin64" instead of bin. `bin64 etc64 intel64 lib64 man ` Users are going to have to go thorough lots of extra runs just to find that path. Maybe it should be added to the path on install instead?
- With many jobs (or even few) the table starts in one state, and then sorts to another - it makes it hard to find things. Why not allow the user to provide a job name, and then click into that group (for a smaller scoped set that doesn't have this changing of state/sorting?)
- Stream logs should be the default unless the run is finished - it's confusing coming here the first time and having it either be empty, paused, or not understanding why it's not showing top down lines of the run (start to finish).
