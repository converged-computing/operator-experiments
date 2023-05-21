# Flux Framework Basic Cluster Deployment

This deployment illustrates deploying a flux-framework cluster on Google Cloud.
All components are included here.

# Usage

Copy the variables to make your own variant:

```bash
$ cp basic.tfvars.example basic.tfvars
```

Make note that the machine types should match those you prepared in [build-images](../../build-images)
Initialize the deployment with the command:

```bash
$ terraform init
```

You'll first want to make your buckets! Edit the script [mkbuckets.sh](mkbuckets.sh)
to your needs. E.g.,:

 - If the bucket already exists, comment out the creation command for it

You'll want to run the script and provide the name of your main bucket (e.g.,
the one with some data to mount):

```bash
$ ./mkbuckets.sh flux-operator-bucket
```
 
It will show an error if it already exists, you can ignore it! Notice a script "fuse-mounts.sh"
will be created - this will mount the bucket to the instances. You can modify the `mkbuckets.sh` script
to do other tasks that you want your instance to do on startup too. Then, deploy the cluster with the command:

```bash
terraform apply -var-file basic.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=foundation-net \
  -var zone=us-central1-a
```

This will setup networking and all the instances! Note that
you can change any of the `-var` values to be appropriate for your environment.
Verify that the cluster is up:

```bash
gcloud compute ssh gffw-login-001 --zone us-central1-a
```

Note that the above working has some (not merged yet) fixed for the upstream recipe.
Stay tuned! When you are finished destroy the cluster:

```bash
terraform destroy -var-file basic.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=foundation-net \
  -var zone=us-central1-a
```
