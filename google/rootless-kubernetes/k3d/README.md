# Testing Rootless K3d

This variant is basically [k3s](../k3s) but within docker! Or for our use cases,
[using rootless podman](https://k3d.io/v5.4.9/usage/advanced/podman/?h=podman).
It would be fun to explore using Singularity too, but for now let's try this out.

Note that I didn't get super far - I stopped when I would need to set up an entire
Podman thing with rootless, and I just don't have patience for that, I think
it's annoying. But here is as far as I wanted to go.

I first made an instance on compute engine (my personal account) e2-standard-4
with a 100MB disk (about 0.15 cents per hour). Shell in

```bash
gcloud compute ssh --zone "us-central1-a" "test-rootless-kubernetes" --project "$GOOGLE_PROJECT"
```

## Setup

### Cgroups 2

We need to enable (or make sure that) cgroups version 2 is enabled.
If the file `/sys/fs/cgroup/cgroup.controllers` exists (it does on Google
Cloud) you are good! If not, [follow the instructions here](https://rootlesscontaine.rs/getting-started/common/cgroup2/)
to enable cgroups 2. We also need `cpuset` added to the file:

```
cat /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.controllers
```

Here is how to add the additional permissions:

```
sudo mkdir -p /etc/systemd/system/user@.service.d
cat <<EOF | sudo tee /etc/systemd/system/user@.service.d/delegate.conf
[Service]
Delegate=cpu cpuset io memory pids
EOF
sudo systemctl daemon-reload
```

```diff
- memory pids
+ cpuset cpu io memory pids
```

### Podman

You can install podman as follows:

```bash
sudo apt install podman
```

And then we want to make sure we follow the steps in the [rootless tutorial](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md). Here is a quick test for the crun runtime:

```bash
podman --runtime crun run hello-world
```

Then set this to be the default runtime in `/usr/share/containers/containers.conf`

```bash
sudo vim /usr/share/containers/containers.conf
```
```diff
# Default OCI runtime
#
- # runtime = "crun"
+ runtime = "crun"
```

Ensure `slirp4netns` is installed:

```bash
$ sudo apt-get install -y slirp4netns
```

For some reason I read that and all I see is "slurpy-for-nettes" :)

Ensure you have `fuse-overlayfs` (I did)

```bash
$ sudo apt-get install -y fuse-overlayfs
$ which fuse-overlayfs
/usr/bin/fuse-overlayfs
```

Note there is special work needed for user namespaces on [RHEL7 machines](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md#enable-user-namespaces-on-rhel7-machines) and we might eventually be concerned about [ping](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md#enable-unprivileged-ping) (seems kind of random)?

I didn't go through ALL the details for the user-level config files - I'll go back to them
when I need. Ensure it's running:

```bash
sudo systemctl enable --now podman.socket
```

Disable timeout for the service

```bash
sudo mkdir -p /etc/containers/containers.conf.d
sudo vim /etc/containers/containers.conf.d/timeout.conf
```
And write this:
```
service_timeout=0
```

Make a symbolic link to the docker socket:

```bash
sudo ln -s /run/podman/podman.sock /var/run/docker.sock
```

OR (I think actually we want to do this for rootless):

```bash
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock
export DOCKER_SOCK=$XDG_RUNTIME_DIR/podman/podman.sock
```

### k3d

Install it!

```bash
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
```

Try creating a cluster:

```bash
k3d cluster create
```

I got errors, all related to podman, and to be frank I kind of hate rootless podman
so I stopped here. Maybe someone else wants to try (or we can try where someone has
painfully already gone through this setup). I would rather try from scratch 
with Singularity _where things make sense_ and the most I have to worry about
is read only and mounts!
