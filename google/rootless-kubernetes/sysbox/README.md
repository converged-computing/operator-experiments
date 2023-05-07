# sysbox

I first made an instance on compute engine (my personal account) e2-standard-4
with a 100MB disk (about 0.15 cents per hour). Shell in

```bash
gcloud compute ssh --zone "us-central1-a" "test-rootless-kubernetes" --project "$GOOGLE_PROJECT"
```

I'm following instructions from [here](https://github.com/nestybox/sysbox/blob/master/docs/user-guide/install-package.md).

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


### Docker

We need to install docker

```bash
sudo apt update
sudo apt install --yes apt-transport-https ca-certificates curl gnupg2 software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"
sudo apt update
sudo apt install --yes docker-ce
sudo usermod -aG docker $USER
```

You can log out/in to be able to use it without sudo.

### Sysbox

Now [install sysbox](https://github.com/nestybox/sysbox/blob/master/docs/user-guide/install-package.md)

```bash
$ sudo apt-get install -y linux-headers-$(uname -r)
$ sudo apt-get install -y wget jq rsync fuse
$ wget https://downloads.nestybox.com/sysbox/releases/v0.6.1/sysbox-ce_0.6.1-0.linux_amd64.deb
$ sudo dpkg -i sysbox-ce_0.6.1-0.linux_amd64.deb
```

Note that I saw this warning, which I'm sure we need to be concerned about later!

> Your OS does not support 'idmapped' feature (kernel < 5.12), nor it  provides 'shiftfs' support. In consequence, applications within Sysbox  containers may be unable to access volume-mounts, which will show up as  owned by 'nobody:nogroup' inside the container. Refer to Sysbox  installation documentation for details.

Verify they are running:

```bash
sudo systemctl status sysbox -n20
```

But note that the last component for the filesystem is missing. I think [this bug should be fixed soon](https://forums.docker.com/t/sysbox-runc-native-support-now-that-docker-has-bought-nestybox/130939/3) but I'm going to stop here.
We would next start kubeadm on the control node.
