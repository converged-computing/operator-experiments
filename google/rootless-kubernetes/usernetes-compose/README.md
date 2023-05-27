# usernetes-compose

I asked if [there could be support for multiple hosts](https://github.com/rootless-containers/usernetes/issues/281)
and indeed this was possible. I first wanted to try this docker-compose setup. We will
follow the instructions [here](https://github.com/rootless-containers/usernetes/tree/v20230518.0#multi-node-docker-compose).
The goal here is to understand what CIDR addresses are and how we can extend this functionality
to k3s.

## Setup

Clone the repository at this release.

```bash
$ git clone -b v20230518.0 https://github.com/rootless-containers/usernetes
cd usernetes
make up
```

When the cluster is donec creating (and the kubeconfig file will be saved to your host)
you'll want to set it and then use it. E.g.,

```bash
$ export KUBECONFIG=$HOME/.config/usernetes/docker-compose.kubeconfig
```
And then it works!

```
$ kubectl get nodes
NAME              STATUS   ROLES    AGE     VERSION
node-containerd   Ready    <none>   2m20s   v1.27.2
node-crio         Ready    <none>   2m20s   v1.27.2
```

Nice!

When you are done playing around:

```bash
$ make down
```

From this point on I want to build this into VMs in  [this repository](https://github.com/converged-computing/flux-terraform-gcp).
