# Flux Framework LAMMPS Cluster Deployment

This deployment illustrates deploying a flux-framework cluster on Google Cloud
to run LAMMPS. All components are included here.

# Usage

Copy the variables to make your own variant:

```bash
$ cp lammps.tfvars.example lammps.tfvars
```

Make note that the machine types should match those you prepared in [build-images](../../build-images)
Initialize the deployment with the command:

```bash
$ terraform init
```

Since LAMMPS does not need a shared file system, we won't be mounting any buckets.

## Deploy

Then, deploy the cluster with the command:

```bash
$ terraform apply -var-file lammps.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=foundation-net \
  -var zone=us-central1-a
```

This will setup networking and all the instances! Note that
you can change any of the `-var` values to be appropriate for your environment.
Verify that the cluster is up:

```bash
$ gcloud compute ssh gffw-login-001 --zone us-central1-a
```

## Run Experiments

The easiest thing to do is to copy the file to run experiments to your home directory!

```bash
$ gcloud compute scp --zone us-central1-a ./run-experiments.py gffw-login-001:/home/sochat1_llnl_gov/run-experiments.py
```

And then shell in (as we did above)


```bash
$ gcloud compute ssh gffw-login-001 --zone us-central1-a
```

Go to the experiment directory with our files of interest

```bash
cd /opt/lammps/examples/reaxff/HNS
```

Try running the lammps experiment, given that lammps is installed on the nodes, and (for this example) we have two nodes only.
Note that by default, output data will be written to the present working directory in a "data" subfolder. Since
we don't have write in the experiment files folder, we direct to our home directory (it will be created):

```bash
$ python3 $HOME/run-experiments.py --outdir /home/sochat1_llnl_gov/data \
          --workdir /opt/lammps/examples/reaxff/HNS \
          --times 10 -N 2 --tasks 2 lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
```

<details>

<summary>Example Output</summary>

```console
         N: 2
     times: 10
     sleep: 10
    outdir: /home/sochat1_llnl_gov/data
     tasks: 2
   command: lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
   workdir: /opt/lammps/examples/reaxff/HNS
   dry-run: False
identifier: lammps
Submit ƒ31XLJ9fgb: 1 of 10
Submit ƒ31XQvVRh1: 2 of 10
Submit ƒ31XVVsD8j: 3 of 10
Submit ƒ31Xa6iyro: 4 of 10
Submit ƒ31Xehakas: 5 of 10
Submit ƒ31XjKvWbH: 6 of 10
Submit ƒ31XovnHKM: 7 of 10
Submit ƒ31XtXe43R: 8 of 10
Submit ƒ31XyCwncX: 9 of 10
Submit ƒ31Y439Ssh: 10 of 10

⭐️ Waiting for jobs to finish...
    Still waiting on job ƒ31XLJ9fgb, has state RUN
No longer waiting on job ƒ31XLJ9fgb, FINISHED 0!
    Still waiting on job ƒ31XQvVRh1, has state RUN
No longer waiting on job ƒ31XQvVRh1, FINISHED 0!
    Still waiting on job ƒ31XVVsD8j, has state RUN
No longer waiting on job ƒ31XVVsD8j, FINISHED 0!
    Still waiting on job ƒ31Xa6iyro, has state RUN
No longer waiting on job ƒ31Xa6iyro, FINISHED 0!
    Still waiting on job ƒ31Xehakas, has state RUN
No longer waiting on job ƒ31Xehakas, FINISHED 0!
    Still waiting on job ƒ31XjKvWbH, has state RUN
No longer waiting on job ƒ31XjKvWbH, FINISHED 0!
    Still waiting on job ƒ31XovnHKM, has state RUN
No longer waiting on job ƒ31XovnHKM, FINISHED 0!
    Still waiting on job ƒ31XtXe43R, has state RUN
No longer waiting on job ƒ31XtXe43R, FINISHED 0!
    Still waiting on job ƒ31XyCwncX, has state RUN
No longer waiting on job ƒ31XyCwncX, FINISHED 0!
    Still waiting on job ƒ31Y439Ssh, has state RUN
No longer waiting on job ƒ31Y439Ssh, FINISHED 0!
Jobs are complete, goodbye! 👋️
```

</details>

The script will hang after the last run waiting for the jobs to finish.
And that's it! The output directory in your home will have both log files (from the job output and error)
and the job info (json) from Flux:

```bash
$ ls /home/sochat1_llnl_gov/data/
```
```console
lammps-0-info.json  lammps-2-info.json  lammps-4-info.json  lammps-6-info.json  lammps-8-info.json
lammps-0.log        lammps-2.log        lammps-4.log        lammps-6.log        lammps-8.log
lammps-1-info.json  lammps-3-info.json  lammps-5-info.json  lammps-7-info.json  lammps-9-info.json
lammps-1.log        lammps-3.log        lammps-5.log        lammps-7.log        lammps-9.log
```

When you exit from the node, you can copy this to your computer to save.

```bash
$ mkdir -p ./data
$ gcloud compute scp --zone us-central1-a gffw-login-001:/home/sochat1_llnl_gov/data/* ./data
```

And that's really it :) When you are finished destroy the cluster:


```bash
$ terraform destroy -var-file lammps.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=foundation-net \
  -var zone=us-central1-a
```
