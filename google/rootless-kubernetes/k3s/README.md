# Testing Rootless K3s

I first made an instance on compute engine (my personal account) e2-standard-4
with a 100MB disk (about 0.15 cents per hour). Shell in

```bash
gcloud compute ssh --zone "us-central1-a" "test-rootless-kubernetes" --project "$GOOGLE_PROJECT"
```

Note that k3s already has [k3d](https://github.com/k3d-io/k3d), which is the same thing in Docker!
We likely can't use docker on our systems, but given we know it works in containers, this could be a good
start!

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

### k3s

You'll need wget and uidmap

```bash
sudo apt-get update && sudo apt-get install -y wget uidmap
```

Install K3s as follows:

```bash
curl -sfL https://get.k3s.io | sh -
```

This should install k3s

```bash
$ which k3s
/usr/local/bin/k3s
```

Install the rootless service:

```bash
$ wget https://raw.githubusercontent.com/k3s-io/k3s/master/k3s-rootless.service
$ mkdir -p ~/.config/systemd/user
$ sudo mv ./k3s-rootless.service ~/.config/systemd/user/k3s-rootless.service
```

Note that the `ExecStart` in the service above assumes the install is to `/usr/local/bin/k3s`

```bash
systemctl --user daemon-reload
systemctl --user enable --now k3s-rootless
```

Note there are [advanced configuration options](https://docs.k3s.io/advanced#advanced-rootless-configuration) as well.

You should check that the service is running:

```bash
$ systemctl --user status k3s-rootless
● k3s-rootless.service - k3s (Rootless)
     Loaded: loaded (/home/vanessa/.config/systemd/user/k3s-rootless.service; enabled; vendor preset: enabled)
     Active: active (running) since Fri 2023-05-05 20:24:26 UTC; 19s ago
   Main PID: 4769 (k3s-server)
      Tasks: 56
     Memory: 403.2M
        CPU: 25.639s
     CGroup: /user.slice/user-1000.slice/user@1000.service/app.slice/k3s-rootless.service
             └─k3s_evac
               ├─4769 /usr/local/bin/k3s server
               ├─4785 /proc/self/exe init
               ├─4797 slirp4netns --mtu 65520 -r 3 --disable-host-loopback --cidr 10.41.0.0/16 4785 tap0
               ├─4800 k3s server
               └─4823 k3s server
```

If you need to debug, journalctl is helpful!

```bash
journalctl --user -f -u k3s-rootless
```

### Config

Finally, we will want a config to be written automatically. if you just did `kubectl get nodes` 
it would show that the `/etc/rancher...` config isn't writable, but we actually don't want to change that.
We want to do:

```
export KUBECONFIG=~/.kube/config
mkdir ~/.kube 2> /dev/null
sudo k3s kubectl config view --raw > "$KUBECONFIG"
chmod 600 "$KUBECONFIG"
```

And make sure to add this to your bash profile so it loads on restart:

```bash
echo "export KUBECONFIG=~/.kube/config" >> ~/.profile
```

Now you can get nodes:

```
$ kubectl get nodes
NAME                      STATUS   ROLES                  AGE   VERSION
test-rootless-kubenetes   Ready    control-plane,master   23h   v1.26.4+k3s1
```

Yay! Next I think we want to try building this into a container with Flux. I
want to keep [this issue](https://stackoverflow.com/questions/72706976/run-k3s-in-rootless-mode)
in mind too.
