import argparse
import inspect
import json
import os

import jinja2
from google.cloud import batch_v1, storage

# Script templates

run_script = """#!/bin/bash
export PATH=/opt/intel/mpi/latest/bin:$PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/intel/mpi/latest/lib:/opt/intel/mpi/latest/lib/release
source /opt/intel/mpi/latest/env/vars.sh

# Ensure we have the wrapper template and it's correctly populated
wrapper={{ mount_path }}/{{ outdir }}/netmark_wrapper.sh
cat ${wrapper}
chmod +x ${wrapper}

if [ $BATCH_TASK_INDEX = 0 ]; then
  cd {{ mount_path }}/{{ outdir }}
  ls
  mpirun -n {{ tasks }} -ppn {{ tasks_per_node }} -f $BATCH_HOSTS_FILE ${wrapper}
fi
"""

wrapper = """#!/bin/bash
{{mount_path}}/{{netmark_path}}/netmark.x -w {{warmup}} -t {{trials}} -c {{cycles}} -b {{message_size}} {% if store_trial %} -s {% endif %}
"""

setup_script = """#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
sleep $BATCH_TASK_INDEX

# Note that for this family / image, we are root (do not need sudo)
yum update -y && yum install -y cmake gcc tuned ethtool python3

# Ensure a python3 executable is found, if does not exist
which python3 || (ln -s $(which python) /usr/bin/python3)

# This ONLY works on the hpc-* image family images
google_mpi_tuning --nosmt
# google_install_mpi --intel_mpi
google_install_intelmpi --impi_2021
source /opt/intel/mpi/latest/env/vars.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/intel/mpi/latest/lib:/opt/intel/mpi/latest/lib/release
export PATH=/opt/intel/mpi/latest/bin:$PATH
outdir={{ mount_path }}/{{outdir}}
mkdir -p $outdir
find /opt/intel -name mpicc

# Only have index 0 compile
if [ $BATCH_TASK_INDEX = 0 ]; then
  cd {{ mount_path }}/{{netmark_path}}
  ls
  # And only compile if the executable does not exist!   
  # Makefile content plus adding include directories
  if [[ ! -f "netmark.x" ]]; then
      mpicc -std=c99 -lmpi -lmpifort -O3 netmark.c -DTRACE -I/opt/intel/mpi/latest/include -I/opt/intel/mpi/2021.8.0/include -L/opt/intel/mpi/2021.8.0/lib/release -L/opt/intel/mpi/2021.8.0/lib -o netmark.x 
   fi
fi
"""


def get_parser():
    parser = argparse.ArgumentParser(
        description="Netmark BATCH",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("project", help="Google cloud project")
    parser.add_argument("--region", help="Google cloud region", default="us-central1")

    # Be careful changing this - the Google MPI won't work on debian
    parser.add_argument(
        "--image-family", help="Google cloud image family", default="hpc-centos-7"
    )
    parser.add_argument(
        "--image-project",
        help="Google cloud image project",
        default="cloud-hpc-image-public",
    )

    parser.add_argument(
        "--job-name", dest="job_name", help="Name for the job", default="netmark-job"
    )
    parser.add_argument(
        "--bucket", help="Bucket that netmark code is in", required=True
    )

    # mpitune configurations are validated on c2 and c2d instances only.
    parser.add_argument(
        "--machine-type",
        help="Google cloud machine type / VM",
        default="c2-standard-16",
    )
    parser.add_argument(
        "--netmark-path",
        dest="netmark_path",
        help="Relative path of netmark code in bucket",
        default="netmark",
    )
    parser.add_argument(
        "--outdir",
        help="output directory for results (relative to bucket)",
        default="data",
    )
    parser.add_argument(
        "--mount-path",
        help="mount location for bucket in VM",
        default="/mnt/share",
    )
    parser.add_argument("--tasks", help="number of tasks (nodes)", type=int, default=4)
    parser.add_argument(
        "--cpu-milli", help="milliseconds per cpu-second", type=int, default=1000
    )
    parser.add_argument(
        "--tasks-per-node", help="tasks per node (N)", type=int, default=1
    )
    parser.add_argument("--memory", help="memory in MiB", type=int, default=1000)  # 1GB
    parser.add_argument("--retry-count", help="retry count", type=int, default=2)  # 1GB
    parser.add_argument(
        "--max-run-duration",
        help="maximum run duration, string (e.g., 3600s)",
        default="3600s",
    )  # 1GB
    parser.add_argument(
        "--parallelism",
        help="Parallelism of tasks",
        default=1,
        type=int,
    )  # 1GB
    # These arguments map directly to netmark
    # The defaults are the ones we see set in the example
    # /mnt/share/{{netmark_path}}/netmark.x -w 10 -t 20 -c 100 -b 0 -s
    parser.add_argument(
        "--netmark-warmup",
        dest="warmup",
        help="number of warmups",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--netmark-trials", dest="trials", help="number of trials", type=int, default=20
    )
    parser.add_argument(
        "--netmark-send-recv-cycles",
        dest="cycles",
        help="number of send receive cycles",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--netmark-message-size",
        dest="message_size",
        help="message size in bytes (B)",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--netmark-store-trial",
        dest="store_trial",
        help="store each trial flag",
        action="store_true",
        default=False,
    )
    return parser


# pip install --upgrade google-cloud-storage.
def upload_to_bucket(blob_name, path_to_file, bucket_name):
    """
    Upload script file to a bucket
    """
    storage_client = storage.Client()

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(path_to_file)
    return blob.public_url


def main():
    """
    Run a netmark experiment using Google batch.
    """
    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, _ = parser.parse_known_args()

    # Let's write one big stupid function like in the example!
    job = batch_job(
        args.project,
        args.region,
        args.job_name,
        bucket_name=args.bucket,
        netmark_path=args.netmark_path,
        machine_type=args.machine_type,
        image_family=args.image_family,
        image_project=args.image_project,
        outdir=args.outdir,
        tasks=args.tasks,
        tasks_per_node=args.tasks_per_node,
        cpu_milli=args.cpu_milli,
        memory=args.memory,
        retry_count=args.retry_count,
        max_run_duration=args.max_run_duration,
        mount_path=args.mount_path,
        parallelism=args.parallelism,
        # Netmark Arguments
        warmup=args.warmup,
        trials=args.trials,
        cycles=args.cycles,
        message_size=args.message_size,
        store_trial=args.store_trial,
    )
    print("Submit Job!")
    print(job)


def template_and_write(local_path, template, bucket_name, bucket_path=None):
    """
    Write script to a local path, and upload to bucket
    """
    bucket_path = bucket_path or local_path
    dirname = os.path.dirname(local_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(local_path, "w") as fd:
        fd.write(template)
    upload_to_bucket(bucket_path, local_path, bucket_name)


def batch_job(
    project_id: str,
    region: str,
    job_name: str,
    bucket_name: str,
    netmark_path: str,
    outdir: str,
    tasks: int,
    tasks_per_node: int,
    cpu_milli: int,
    memory: int,
    retry_count: int,
    machine_type: str,
    image_family: str,
    image_project: str,
    max_run_duration: str,
    mount_path: str,
    warmup: int,
    trials: int,
    cycles: int,
    message_size: int,
    store_trial: int,
    parallelism: int,
) -> batch_v1.Job:
    """
    Create a Netmark Job, building netmark from mounted code in a Google Bucket.

    Protos (for looking at options) can be found at:
    https://github.com/googleapis/googleapis/blob/master/google/cloud/batch/v1alpha
    """
    client = batch_v1.BatchServiceClient()

    # Get all metadata for function
    sig, batch_job_locals = inspect.signature(batch_job), locals()
    metadata = {
        param.name: batch_job_locals[param.name] for param in sig.parameters.values()
    }

    # Output directory should include the job name for uniqueness
    outdir = os.path.join(outdir, job_name)

    # Prepare the script templates
    run_template = jinja2.Template(run_script)
    runscript = run_template.render(
        {
            "mount_path": mount_path,
            "tasks": tasks,
            "tasks_per_node": tasks_per_node,
            "netmark_path": netmark_path,
            "outdir": outdir,
        }
    )
    # Prepare the wrapper template
    wrapper_template = jinja2.Template(wrapper)
    wrapper_script = wrapper_template.render(
        {
            "netmark_path": netmark_path,
            "mount_path": mount_path,
            "warmup": warmup,
            "trials": trials,
            "cycles": cycles,
            "message_size": message_size,
            "store_trial": store_trial,
        }
    )

    setup_template = jinja2.Template(setup_script)
    script = setup_template.render(
        {"netmark_path": netmark_path, "outdir": outdir, "mount_path": mount_path}
    )

    # Scripts are scoped to their job path, this is relative to storage
    setup_path = os.path.join(outdir, "setup.sh")
    run_path = os.path.join(outdir, "run.sh")
    wrapper_path = os.path.join(outdir, "netmark_wrapper.sh")
    metadata_path = os.path.join(outdir, "metadata.json")

    # Write over same file here, yes bad practice and lazy
    template_and_write(setup_path, script, bucket_name)
    template_and_write(run_path, runscript, bucket_name)
    template_and_write(wrapper_path, wrapper_script, bucket_name)
    template_and_write(metadata_path, json.dumps(metadata, indent=4), bucket_name)

    # Define what will be done as part of the job.
    task = batch_v1.TaskSpec()
    setup = batch_v1.Runnable()
    setup.script = batch_v1.Runnable.Script()
    setup.script.text = f"bash {mount_path}/{setup_path}"

    # This will ensure all nodes finish first
    barrier = batch_v1.Runnable()
    barrier.barrier = batch_v1.Runnable.Barrier()
    barrier.barrier.name = "wait-for-setup"

    runnable = batch_v1.Runnable()
    runnable.script = batch_v1.Runnable.Script()
    runnable.script.text = f"bash {mount_path}/{run_path}"

    # If parallelism == 1, no barriers as running on same instance
    if parallelism == 1:
        task.runnables = [setup, runnable]
    else:
        task.runnables = [barrier, setup, barrier, runnable]

    gcs_bucket = batch_v1.GCS()
    gcs_bucket.remote_path = bucket_name
    gcs_volume = batch_v1.Volume()
    gcs_volume.gcs = gcs_bucket
    gcs_volume.mount_path = mount_path
    task.volumes = [gcs_volume]

    # We can specify what resources are requested by each task.
    resources = batch_v1.ComputeResource()

    # in milliseconds per cpu-second. The requirement % of a single CPUs.
    resources.cpu_milli = cpu_milli
    resources.memory_mib = memory
    task.compute_resource = resources

    task.max_retry_count = retry_count
    task.max_run_duration = max_run_duration

    # Tasks are grouped inside a job using TaskGroups.
    # Currently, it's possible to have only one task group.
    group = batch_v1.TaskGroup()
    group.task_count_per_node = tasks_per_node
    group.task_count = tasks
    group.task_spec = task
    group.parallelism = parallelism
    group.require_hosts_file = True
    group.permissive_ssh = True

    # Disks is how we specify the image we want (we need centos to get MPI working)
    # This could also be batch-centos, batch-debian, batch-cos but MPI won't work on all of those
    boot_disk = batch_v1.AllocationPolicy.Disk()
    boot_disk.image = f"projects/{image_project}/global/images/family/{image_family}"

    # Policies are used to define on what kind of virtual machines the tasks will run on.
    # https://github.com/googleapis/python-batch/blob/main/google/cloud/batch_v1/types/job.py#L383
    allocation_policy = batch_v1.AllocationPolicy()
    policy = batch_v1.AllocationPolicy.InstancePolicy()
    policy.machine_type = machine_type
    policy.boot_disk = boot_disk

    instances = batch_v1.AllocationPolicy.InstancePolicyOrTemplate()
    instances.policy = policy
    allocation_policy.instances = [instances]

    job = batch_v1.Job()
    job.task_groups = [group]
    job.allocation_policy = allocation_policy
    job.labels = {"env": "testing", "type": "script", "mount": "bucket"}

    # We use Cloud Logging as it's an out of the box available option
    job.logs_policy = batch_v1.LogsPolicy()
    job.logs_policy.destination = batch_v1.LogsPolicy.Destination.CLOUD_LOGGING

    create_request = batch_v1.CreateJobRequest()
    create_request.job = job
    create_request.job_id = job_name

    # The job's parent is the region in which the job will run
    create_request.parent = f"projects/{project_id}/locations/{region}"
    return client.create_job(create_request)


if __name__ == "__main__":
    main()
