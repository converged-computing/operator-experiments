# k3s-docker-compose

This repo comes from the post here: [Setup Local Integration Environment with K3s and Docker Compose](https://rocky-chen.medium.com/setup-local-integration-environment-with-k3s-and-docker-compose-13fd815765cc). My plan is that if I can get this working
in Docker Compose, Singularity Compose could be an option too (or more generally, Singularity containers
actually orchestrated under Flux). I decided to modify this to use a public registry instead of local
because I wasn't comfortable tweaking my local setup.

## Usage

Create the setup:

```bash
$ make integration-up
```

Here is how to interact with the cluster via kubectl to see logs, etc.:

```bash
$ kubectl --kubeconfig=./kubeconfig.yaml get pods
```
```console
NAME                       READY   STATUS    RESTARTS   AGE
my-echo-74dc6c4f7b-xpcbb   1/1     Running   0          72s
```

And the deployment:

```bash
$ kubectl --kubeconfig=./kubeconfig.yaml get deploy
```
```console
NAME      READY   UP-TO-DATE   AVAILABLE   AGE
my-echo   1/1     1            1           98s
```


You should see the whole thing build, push, and then deploy!

<details>

<summary>The Deployment!</summary>

```bash
Start K3s cluster and registry locally.
docker-compose up -d
k3s-docker-compose_server_1 is up-to-date
k3s-docker-compose_registry_1 is up-to-date
k3s-docker-compose_agent_1 is up-to-date

Build application image.
docker build . -t "docker.io/vanessa/my-echo:"latest""
[+] Building 0.1s (5/5) FINISHED                                                                                                                               
 => [internal] load build definition from Dockerfile                                                                                                      0.0s
 => => transferring dockerfile: 82B                                                                                                                       0.0s
 => [internal] load .dockerignore                                                                                                                         0.0s
 => => transferring context: 2B                                                                                                                           0.0s
 => [internal] load metadata for gcr.io/google-containers/echoserver:1.8                                                                                  0.1s
 => CACHED [1/1] FROM gcr.io/google-containers/echoserver:1.8@sha256:cb3386f863f6a4b05f33c191361723f9d5927ac287463b1bea633bf859475969                     0.0s
 => exporting to image                                                                                                                                    0.0s
 => => exporting layers                                                                                                                                   0.0s
 => => writing image sha256:43e8ef024793ebe6c541e022ab0bb51d8a0f2b5ba4a102f36617757bf6034057                                                              0.0s
 => => naming to docker.io/vanessa/my-echo:latest                                                                                                         0.0s

Push image to local registry.
docker push "docker.io/vanessa/my-echo:"latest""
The push refers to repository [docker.io/vanessa/my-echo]
e501a733ae34: Layer already exists 
e6ce2efbc7ee: Layer already exists 
e09c2d7e6d07: Layer already exists 
cc672f0d03c0: Layer already exists 
9eba96aca12d: Layer already exists 
74da00cb2e0b: Layer already exists 
3492e63eae81: Layer already exists 
4abdb672ab53: Layer already exists 
latest: digest: sha256:72edf690349362f28b33fd38f1bb1183372e2f3743f38aa50db71d50c31c976d size: 1986

Apply Deployment and Service definitions to K3s cluster.
kubectl --kubeconfig=./kubeconfig.yaml apply -f my-echo.yaml
service/my-echo created
deployment.apps/my-echo created

Waiting for deployment done.
until kubectl --kubeconfig=./kubeconfig.yaml rollout status deployment my-echo; do sleep 1; done
Waiting for deployment "my-echo" rollout to finish: 0 of 1 updated replicas are available...
deployment "my-echo" successfully rolled out
```

</details>

I think I'm going to try this with Singularity compose next!
