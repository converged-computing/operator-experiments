# Flux Framework + K3S Basic Cluster Deployment

This is going to test K3s on a "bare metal" VM deployment with Flux.
You should have [built images first](../../bare-metal-comparison/compute-engine/build-images/).
Note that this is currently not working because the Google Build service was down.
I was able to manually create images with cgroups version 2 enabled (details below)
but without the Google Build setup the correct start of flux doesn't seem to be
working. So these images need to be updated as follows:

1. Get the Google Build working with cgroups version 2 added
2. The logic in the boot script here should enable k3s
3. Double check that flux is working (there was a munge key missing)


# Usage

This first section will create us a simple cluster with a login node,
a manager node, and a few compute nodes. First, copy the variables to make your own variant:

```bash
$ cp basic.tfvars.example basic.tfvars
```

Initialize the deployment with the command:

```bash
$ terraform init
```

Note that the script [install_k3s.sh](install_k3s.sh) is run on each node,
and will be required for us to start the cluster. Also note
that I had to manually create these images to enable cgroups, and use a custom terraform recipe
on my branch (on researchapps) and then manually create the new image with a family
from the stopped disk (and this requires creating a new image!) To do this I:

1. Went to Compute Engine -> Images
2. Create an instance from each
3. Install cgroups v2 (instructions below)
4. Stop the instances
5. Under Compute Engine -> Image "Create an Image"
6. Create each one from Source Disk from the image Don't forget to use the same prefix for the family (e.g., flux-cgroups-manager-x86-052123 has family flux-cgroups-manager).

Here is what I needed to run on each image before stopping:

```bash
# This is what I ran manually to update the machines and save new images
sudo dnf install -y grubby 
sudo grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=1"

sudo mkdir -p /etc/systemd/system/user@.service.d
cat <<EOF | sudo tee /etc/systemd/system/user@.service.d/delegate.conf
[Service]
Delegate=cpu cpuset io memory pids
EOF
sudo systemctl daemon-reload
```

Note that if cgroups 2 is enabled you should have this file:

```
cat /sys/fs/cgroup/cgroup.controllers
cpuset cpu io memory hugetlb pids rdma
```

## Customize

### Automated

**not working yet!**

Note this doesn't seem to be working yet because the startup script logic is not working -
we likely need to step back and get the cloud build image working with cgroups v2 first,
and the come back to this. For now, you need to do the manual setup. Sorry!

I wrote a fairly janky setup script for k3s, and you should look at [install_k3s.sh](install_k3s.sh).
I currently hard coded my user name as the intended user (because that was easiest) but I think
a better approach would be to separate the user-specific steps from the k3s install steps,
and then allow any user to shell in to use it. For now since we are playing around,
you can change these lines:

```bash
# CHANGE THIS TO SOMETHING DIFFERENT!
secret_token=pancakes-chicken-finger-change-me
username=sochat1_llnl_gov
##
```

### Manual

See the [manual setup](#manual-setup) that needs to be run after you create the cluster.
This isn't ideal, but my hack to get cgroups 2 installed didn't seem to bring with it the
ability to add a boot script, so it's what I'm doing for now. Please feel free to fix this
up when Google Build is working again.

## Deploy

Then, deploy the cluster with the command:

```bash
terraform apply -var-file basic.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=basic-k3s-net \
  -var zone=us-central1-a
```

This will setup networking and all the instances! Note that
you can change any of the `-var` values to be appropriate for your environment.
Verify that the cluster is up and login:

```bash
gcloud compute ssh k3s-login-001 --zone us-central1-a
```

And then check that your cluster is running. You should see the compute nodes
as workers and ready for service!

## Manual Setup

This is the approach you'll need to take for login and worker nodes until the startup / boot
script seems to take. Sorry, I wanted to do other stuff today and don't want to debug this many
layers into Google Cloud.

#### Login Node

These steps should be run on your login node!

```bash
gcloud compute ssh k3s-login-001 --zone us-central1-a
```
```bash
export secret_token=pancakes-chicken-finger-change-me

sudo dnf update -y 
sudo dnf install -y wget bind-utils

wget https://raw.githubusercontent.com/k3s-io/k3s/master/k3s-rootless.service
mkdir -p ~/.config/systemd/user
mv ./k3s-rootless.service ~/.config/systemd/user/k3s-rootless.service

# We might be able to do this?
curl -sfL https://get.k3s.io | K3S_TOKEN=${secret_token} sh -

export KUBECONFIG=~/.kube/config
mkdir ~/.kube

# TODO double check if this config is correct for rootless mode!
sudo cp /etc/rancher/k3s/k3s.yaml /home/$username/.kube/config

# Get the kubeconfig to use
echo "export KUBECONFIG=~/.kube/config" >> ~/.bash_profile

# Reload!
systemctl --user daemon-reload
systemctl --user enable --now k3s-rootless
sudo chown -R $USER ~/.kube/ ~/.config

# With just the master this will show just the control plane
# kubectl get nodes
```

#### Worker Nodes

These steps should be run on your worker nodes!

```bash
gcloud compute ssh k3s-compute-a-001 --zone us-central1-a
```

```bash
export secret_token=pancakes-chicken-finger-change-me

sudo dnf update -y 
sudo dnf install -y bind-utils

# Note the login node hostname is hard coded here!!
login_node=$(nslookup k3s-login-001 | grep Address |  sed -n '2 p' |  sed 's/Address: //g')
echo "Login node is ${login_node}"
curl -sfL https://get.k3s.io | K3S_URL=https://${login_node}:6443 K3S_TOKEN=${secret_token} sh -
```

#### Back to Login...

Back on the login node, you should be able to see your nodes:

```bash
gcloud compute ssh k3s-login-001 --zone us-central1-a
```
```bash
kubectl get nodes
```
```console
$ kubectl  get nodes
NAME                STATUS   ROLES                  AGE   VERSION
k3s-login-001       Ready    control-plane,master   22m   v1.26.4+k3s1
k3s-compute-a-001   Ready    <none>                 40s   v1.26.4+k3s1
```

HUZZAH! Flux seems to be broken in this setup:

```
sudo journalctl -f
```

Which I think is related to not using the Google Cloud build (missing the metadata steps)
But when that works, I think you'll have a Flux cluster WITH k3s. yay!
Try deploying something:

```bash
wget https://raw.githubusercontent.com/flux-framework/flux-operator/main/examples/nested/k3s/basic/my-echo.yaml
```
```bash
$ kubectl apply -f my-echo.yaml 
service/my-echo created
deployment.apps/my-echo created
```
```bash
$ kubectl get deployment
NAME      READY   UP-TO-DATE   AVAILABLE   AGE
my-echo   1/1     1            1           26s
```

## Cluster

```bash
$ kubectl get nodes
```

Note that this node you are on is designated as the master or control-plan,
so that's where you want to login to run `kubectl` commands. Now, have fun!
When you are finished destroy the cluster:

```bash
terraform destroy -var-file basic.tfvars \
  -var region=us-central1 \
  -var project_id=$(gcloud config get-value core/project) \
  -var network_name=foundation-net \
  -var zone=us-central1-a
```
