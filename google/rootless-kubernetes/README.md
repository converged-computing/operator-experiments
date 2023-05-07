# Rootless Kubernetes

This is an investigation around different (existing) tools that would let us deploy a rootless control plan.
I think I'll first narrow down tools based on being able to support adding multiple different nodes (actual machines)
to the cluster, and then:

1. Test creating the control plan
2. Of a subset of the above, test adding nodes (requires more Google Cloud resources)

I'm using my personal account for now so I'm being conservative, and likely I'll pursue one idea fully until I get stuck or annoyed and try something else!

## Contenders

### Likely Yes

 - [K3s](k3s): This was fairly easy to use to set up a rootless control plane, and I think next we would want to try adding nodes, running something, and 
 then seeing if this is possible to instantiate under Flux. Knowing how this works means we could implement it in a container (see next bullet...)
 - [K3D with rootless Podman](https://k3d.io/v5.4.9/usage/advanced/podman/?h=podman): this could actually be something we could try out of the box. The main flux job would need to launch a batch, where each worker launches a container, and there is a main task to bring the cluster together.
 - [K3s docker compose](k3s-docker-compose): if I can get this working with Docker Compose, Singularity compose would be my next thing to try.
 - [sysbox](sysbox)
 - usernetes TBA
 
### Likely No

 - [Kind](https://github.com/kubernetes-sigs/kind/issues/1928) would not work across multiple machines, and likely wouldn't be a good choice.
 - MiniKube: as far as I can tell, the multiple drivers are assuming multi-node cluster on a single machine.
 - [MicroK8s](https://microk8s.io/docs/clustering) does have support for running a cluster across machines, so promising, but I don't see rootless support. I am likely going to try it for learning anyway.

