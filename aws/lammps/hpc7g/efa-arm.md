## EFA Adapter with ARM

To test using an ARM-based EFA adapted, we built [this Dockerfile](https://github.com/aws-samples/aws-efa-eks/blob/main/Dockerfile)
using ARM. You can follow the instructions in the README.md [here](https://github.com/rse-ops/flux-arm/tree/main/spack) 
to create an instance, and then do the following.

```bash
git clone https://github.com/aws-samples/aws-efa-eks
cd aws-efa-eks
```

Note that I changed the base image [because of this](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/cuda-arm64) in the Dockerfile
and also update a signing key. Here is the Dockerfile I used:

```dockerfile
FROM nvidia/cuda:11.2.0-devel-ubuntu20.04
# Note nvcr.io is recommended, but I didn't have a token
#FROM nvcr.io/nvidia/cuda-arm64:11.2.0-devel-ubuntu20.04

ENV EFA_INSTALLER_VERSION=latest
ENV AWS_OFI_NCCL_VERSION=aws
ENV NCCL_TESTS_VERSION=v2.0.0
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/sbsa/3bf863cc.pub
RUN apt-get update -y

# These will be attempted by the script below, do them here
RUN apt-get update && \
    apt-get install -y pciutils \
    environment-modules \
    tcl \
    libnl-3-200 \
    libnl-route-3-dev \
    rdma-core && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --allow-unauthenticated \
    git \
    gcc \
    vim \
    kmod \
    openssh-client \
    openssh-server \
    build-essential \
    curl \
    autoconf \
    libtool \
    gdb \
    automake \
    python3-distutils \
    cmake

# I removed the apt-get clean here it was leading to bugs for the efa installer
# This seems questionable, lol
# ENV HOME /tmp

ENV LD_LIBRARY_PATH=/usr/local/cuda/extras/CUPTI/lib64:/opt/amazon/openmpi/lib:/opt/nccl/build/lib:/opt/amazon/efa/lib:/opt/aws-ofi-nccl/install/lib:$LD_LIBRARY_PATH
ENV PATH=/opt/amazon/openmpi/bin/:/opt/amazon/efa/bin:$PATH

# The Python on ubuntu 20.04 is 3.8.10
RUN curl https://bootstrap.pypa.io/pip/get-pip.py -o /tmp/get-pip.py && python3 /tmp/get-pip.py
RUN pip3 install awscli

#################################################
## Install EFA installer
RUN cd $HOME \
    && curl -O https://efa-installer.amazonaws.com/aws-efa-installer-${EFA_INSTALLER_VERSION}.tar.gz \
    && tar -xf $HOME/aws-efa-installer-${EFA_INSTALLER_VERSION}.tar.gz \
    && cd aws-efa-installer \
    && ./efa_installer.sh -y -g -d --skip-kmod --skip-limit-conf --no-verify && \
    dpkg -i /root/aws-efa-installer/DEBS/UBUNTU2004/aarch64/libfabric1-aws_1.18.0amzn2.0_arm64.deb

###################################################
## Install NCCL
RUN git clone https://github.com/NVIDIA/nccl.git /opt/nccl \
    && cd /opt/nccl \
    && make -j src.build CUDA_HOME=/usr/local/cuda \
    NVCC_GENCODE="-gencode=arch=compute_80,code=sm_80 -gencode=arch=compute_75,code=sm_75 -gencode=arch=compute_70,code=sm_70 -gencode=arch=compute_60,code=sm_60"

###################################################
## Install AWS-OFI-NCCL plugin
RUN git clone https://github.com/aws/aws-ofi-nccl.git /opt/aws-ofi-nccl \
    && cd /opt/aws-ofi-nccl \
    && git checkout ${AWS_OFI_NCCL_VERSION} \
    && ./autogen.sh \
    && ./configure --prefix=/opt/aws-ofi-nccl/install \
       --with-libfabric=/opt/amazon/efa/ \
       --with-cuda=/usr/local/cuda \
       --with-nccl=/opt/nccl/build \
       --with-mpi=/opt/amazon/openmpi/ \
    && make && make install

###################################################
## Install NCCL-tests
RUN git clone https://github.com/NVIDIA/nccl-tests.git $HOME/nccl-tests \
    && cd $HOME/nccl-tests \
    && git checkout ${NCCL_TESTS_VERSION} \
    && make MPI=1 \
       MPI_HOME=/opt/amazon/openmpi/ \
       CUDA_HOME=/usr/local/cuda \
       NCCL_HOME=/opt/nccl/build \
       NVCC_GENCODE="-gencode=arch=compute_80,code=sm_80 -gencode=arch=compute_75,code=sm_75 -gencode=arch=compute_70,code=sm_70 -gencode=arch=compute_60,code=sm_60"
```

Note that I ran the above interactively, so it might not reproduce (sorry, didn't want to wait again)
For this error:

```
N: Download is performed unsandboxed as root as file '/root/aws-efa-installer/DEBS/UBUNTU2004/aarch64/libfabric1-aws_1.18.0amzn2.0_arm64.deb' couldn't be accessed by user '_apt'. - pkgAcquire::Run (13: Permission denied)
```

I ran it after:

```
dpkg -i /root/aws-efa-installer/DEBS/UBUNTU2004/aarch64/libfabric1-aws_1.18.0amzn2.0_arm64.deb
```

Note that if you use the previous ubuntu 18.04, womp womp (hence why we updated to the above!)

```console
#0 5.039 = Starting Amazon Elastic Fabric Adapter Installation Script =
#0 5.039 = EFA Installer Version: 1.24.0 =
#0 5.039 
#0 5.043 Unsupported operating system.
#0 5.043 Refer EFA documentation (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/efa.html#efa-amis) for more details on supported OSes.
```

More about [EFA can be found here](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/efa.html#efa-os).
Here is how to build:

```bash
docker buildx build -f Dockerfile --platform linux/arm64 --tag ghcr.io/rse-ops/aws-efa-k8s-device-plugin-arm:v0.3.3 .
```

But I did:

```
docker commit 2b4e6de75ab8 ghcr.io/rse-ops/aws-efa-k8s-device-plugin-arm:v0.3.3
docker push ## EFA Adapter with ARM

To test using an ARM-based EFA adapted, we built [this Dockerfile](https://github.com/aws-samples/aws-efa-eks/blob/main/Dockerfile)
using ARM. You can follow the instructions in the README.md [here](https://github.com/rse-ops/flux-arm/tree/main/spack) 
to create an instance, and then do the following.

```bash
git clone https://github.com/aws-samples/aws-efa-eks
cd aws-efa-eks
```

Note that I changed the base image [because of this](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/cuda-arm64) in the Dockerfile
and also update a signing key. Here is the Dockerfile I used:

```dockerfile
FROM nvidia/cuda:11.2.0-devel-ubuntu20.04
# Note nvcr.io is recommended, but I didn't have a token
#FROM nvcr.io/nvidia/cuda-arm64:11.2.0-devel-ubuntu20.04

ENV EFA_INSTALLER_VERSION=latest
ENV AWS_OFI_NCCL_VERSION=aws
ENV NCCL_TESTS_VERSION=v2.0.0
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/sbsa/3bf863cc.pub
RUN apt-get update -y

# These will be attempted by the script below, do them here
RUN apt-get update && \
    apt-get install -y pciutils \
    environment-modules \
    tcl \
    libnl-3-200 \
    libnl-route-3-dev \
    rdma-core && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --allow-unauthenticated \
    git \
    gcc \
    vim \
    kmod \
    openssh-client \
    openssh-server \
    build-essential \
    curl \
    autoconf \
    libtool \
    gdb \
    automake \
    python3-distutils \
    cmake

# I removed the apt-get clean here it was leading to bugs for the efa installer
# This seems questionable, lol
# ENV HOME /tmp

ENV LD_LIBRARY_PATH=/usr/local/cuda/extras/CUPTI/lib64:/opt/amazon/openmpi/lib:/opt/nccl/build/lib:/opt/amazon/efa/lib:/opt/aws-ofi-nccl/install/lib:$LD_LIBRARY_PATH
ENV PATH=/opt/amazon/openmpi/bin/:/opt/amazon/efa/bin:$PATH

# The Python on ubuntu 20.04 is 3.8.10
RUN curl https://bootstrap.pypa.io/pip/get-pip.py -o /tmp/get-pip.py && python3 /tmp/get-pip.py
RUN pip3 install awscli

#################################################
## Install EFA installer
RUN cd $HOME \
    && curl -O https://efa-installer.amazonaws.com/aws-efa-installer-${EFA_INSTALLER_VERSION}.tar.gz \
    && tar -xf $HOME/aws-efa-installer-${EFA_INSTALLER_VERSION}.tar.gz \
    && cd aws-efa-installer \
    && ./efa_installer.sh -y -g -d --skip-limit-conf --no-verify && \
    dpkg -i /root/aws-efa-installer/DEBS/UBUNTU2004/aarch64/libfabric1-aws_1.18.0amzn2.0_arm64.deb

###################################################
## Install NCCL
RUN git clone https://github.com/NVIDIA/nccl.git /opt/nccl \
    && cd /opt/nccl \
    && make -j src.build CUDA_HOME=/usr/local/cuda \
    NVCC_GENCODE="-gencode=arch=compute_80,code=sm_80 -gencode=arch=compute_75,code=sm_75 -gencode=arch=compute_70,code=sm_70 -gencode=arch=compute_60,code=sm_60"

###################################################
## Install AWS-OFI-NCCL plugin
RUN git clone https://github.com/aws/aws-ofi-nccl.git /opt/aws-ofi-nccl \
    && cd /opt/aws-ofi-nccl \
    && git checkout ${AWS_OFI_NCCL_VERSION} \
    && ./autogen.sh \
    && ./configure --prefix=/opt/aws-ofi-nccl/install \
       --with-libfabric=/opt/amazon/efa/ \
       --with-cuda=/usr/local/cuda \
       --with-nccl=/opt/nccl/build \
       --with-mpi=/opt/amazon/openmpi/ \
    && make && make install

###################################################
## Install NCCL-tests
RUN git clone https://github.com/NVIDIA/nccl-tests.git $HOME/nccl-tests \
    && cd $HOME/nccl-tests \
    && git checkout ${NCCL_TESTS_VERSION} \
    && make MPI=1 \
       MPI_HOME=/opt/amazon/openmpi/ \
       CUDA_HOME=/usr/local/cuda \
       NCCL_HOME=/opt/nccl/build \
       NVCC_GENCODE="-gencode=arch=compute_80,code=sm_80 -gencode=arch=compute_75,code=sm_75 -gencode=arch=compute_70,code=sm_70 -gencode=arch=compute_60,code=sm_60"
```

Note that I ran the above interactively, so it might not reproduce (sorry, didn't want to wait again)
For this error:

```
N: Download is performed unsandboxed as root as file '/root/aws-efa-installer/DEBS/UBUNTU2004/aarch64/libfabric1-aws_1.18.0amzn2.0_arm64.deb' couldn't be accessed by user '_apt'. - pkgAcquire::Run (13: Permission denied)
```

I ran it after:

```
dpkg -i /root/aws-efa-installer/DEBS/UBUNTU2004/aarch64/libfabric1-aws_1.18.0amzn2.0_arm64.deb
```

Note that if you use the previous ubuntu 18.04, womp womp (hence why we updated to the above!)

```console
#0 5.039 = Starting Amazon Elastic Fabric Adapter Installation Script =
#0 5.039 = EFA Installer Version: 1.24.0 =
#0 5.039 
#0 5.043 Unsupported operating system.
#0 5.043 Refer EFA documentation (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/efa.html#efa-amis) for more details on supported OSes.
```

More about [EFA can be found here](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/efa.html#efa-os).
Here is how to build:

```bash
docker buildx build -f Dockerfile --platform linux/arm64 --tag ghcr.io/rse-ops/aws-efa-k8s-device-plugin-arm:v0.3.3 .
```

But I did:

```bash
docker commit 2b4e6de75ab8 ghcr.io/rse-ops/aws-efa-k8s-device-plugin-arm:v0.3.3
docker push ghcr.io/rse-ops/aws-efa-k8s-device-plugin-arm:v0.3.3
```

Note that our image above is missing the binary that the (non-arm based) one has - I found it here:

```
bash-4.2# /usr/bin/efa-k8s-device-plugin 
2023/06/27 00:17:39 Fetching EFA devices.
2023/06/27 00:17:39 device: rdmap0s6,uverbs0,/sys/class/infiniband_verbs/uverbs0,/sys/class/infiniband/rdmap0s6

2023/06/27 00:17:39 EFA Device list: [{rdmap0s6 uverbs0 /sys/class/infiniband_verbs/uverbs0 /sys/class/infiniband/rdmap0s6}]
2023/06/27 00:17:39 Starting FS watcher.
2023/06/27 00:17:39 Starting OS watcher.
2023/06/27 00:17:39 device: rdmap0s6,uverbs0,/sys/class/infiniband_verbs/uverbs0,/sys/class/infiniband/rdmap0s6

2023/06/27 00:17:39 Starting to serve on /var/lib/kubelet/device-plugins/aws-efa-device-plugin.sock
2023/06/27 00:17:39 Registered device plugin with Kubelet
```

Note this is how to get info for efa installed I think?

```
/opt/amazon/efa/bin/fi_info -p efa
```

And we need the device plugin for Kubernetes - this gives us a hint of what we need to build:

```
bash-4.2# /usr/bin/efa-k8s-device-plugin 
2023/06/27 00:17:39 Fetching EFA devices.
2023/06/27 00:17:39 device: rdmap0s6,uverbs0,/sys/class/infiniband_verbs/uverbs0,/sys/class/infiniband/rdmap0s6

2023/06/27 00:17:39 EFA Device list: [{rdmap0s6 uverbs0 /sys/class/infiniband_verbs/uverbs0 /sys/class/infiniband/rdmap0s6}]
2023/06/27 00:17:39 Starting FS watcher.
2023/06/27 00:17:39 Starting OS watcher.
2023/06/27 00:17:39 device: rdmap0s6,uverbs0,/sys/class/infiniband_verbs/uverbs0,/sys/class/infiniband/rdmap0s6

2023/06/27 00:17:39 Starting to serve on /var/lib/kubelet/device-plugins/aws-efa-device-plugin.sock
2023/06/27 00:17:39 Registered device plugin with Kubelet
```

## Figuring out the image

At this point I needed to figure out the image, so (shelling into the same VM) I logged into the registry
that I saw the plugin coming from:

```bash
$ aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 602401143452.dkr.ecr.us-west-2.amazonaws.com
```
And then I was able to pull the plugin image!

```bash
$ docker pull 602401143452.dkr.ecr.us-west-2.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3
```

We can inspect it:

```bash
$ docker inspect 602401143452.dkr.ecr.us-west-2.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3
```
```console
[
    {
        "Id": "sha256:1da680a5d70b76000e11643f2eeb44490adb56860ef8672dc38b330ebeb855e8",
        "RepoTags": [
            "602401143452.dkr.ecr.us-west-2.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3"
        ],
        "RepoDigests": [
            "602401143452.dkr.ecr.us-west-2.amazonaws.com/eks/aws-efa-k8s-device-plugin@sha256:364d46e3e482f7cd03c586a69996348aa0ec8e6ff711d73013fbfba1ceb0b20d"
        ],
        "Parent": "",
        "Comment": "",
        "Created": "2021-02-19T18:43:42.608210537Z",
        "Container": "960db37d07cce62e45e18621ac060365c50b420cf1fb97afdff14f860e12287b",
        "ContainerConfig": {
            "Hostname": "960db37d07cc",
            "Domainname": "",
            "User": "",
            "AttachStdin": false,
            "AttachStdout": false,
            "AttachStderr": false,
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ],
            "Cmd": [
                "/bin/sh",
                "-c",
                "#(nop) ",
                "CMD [\"efa-k8s-device-plugin\"]"
            ],
            "Image": "sha256:f764f9829fd69dd6a00db823d4cf6d51e4d795f42a3b8a95383516c82bda545e",
            "Volumes": null,
            "WorkingDir": "",
            "Entrypoint": null,
            "OnBuild": null,
            "Labels": {}
        },
        "DockerVersion": "19.03.11",
        "Author": "",
        "Config": {
            "Hostname": "",
            "Domainname": "",
            "User": "",
            "AttachStdin": false,
            "AttachStdout": false,
            "AttachStderr": false,
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ],
            "Cmd": [
                "efa-k8s-device-plugin"
            ],
            "Image": "sha256:f764f9829fd69dd6a00db823d4cf6d51e4d795f42a3b8a95383516c82bda545e",
            "Volumes": null,
            "WorkingDir": "",
            "Entrypoint": null,
            "OnBuild": null,
            "Labels": null
        },
        "Architecture": "arm64",
        "Os": "linux",
        "Size": 458987845,
        "VirtualSize": 458987845,
        "GraphDriver": {
            "Data": {
                "LowerDir": "/var/lib/docker/overlay2/6e151505944793187934e8373ae094aa47a1b16a0a5367b8a1b1609d070f87f6/diff:/var/lib/docker/overlay2/05b87ea9ee4686e8dddebbe91a81b3e5b97cc801c8125d4e96703a8b5f73693e/diff",
                "MergedDir": "/var/lib/docker/overlay2/bfd827541968c8ed4577449957aec61f163f6be72d3aa7206ebc361c3edb54d6/merged",
                "UpperDir": "/var/lib/docker/overlay2/bfd827541968c8ed4577449957aec61f163f6be72d3aa7206ebc361c3edb54d6/diff",
                "WorkDir": "/var/lib/docker/overlay2/bfd827541968c8ed4577449957aec61f163f6be72d3aa7206ebc361c3edb54d6/work"
            },
            "Name": "overlay2"
        },
        "RootFS": {
            "Type": "layers",
            "Layers": [
                "sha256:ee98f0ebffb3baadf68147214065bc39edfade919f1e9b496674468d184f8dcb",
                "sha256:cf05ef813a2522b7caae7a5d40834e42c31424c8509d70fa5ae814251461b320",
                "sha256:bce5c81faa5fc0d1832ca57e4b2a14d9f474084b4ee67d2d5e01e41051b16914"
            ]
        },
        "Metadata": {
            "LastTagTime": "0001-01-01T00:00:00Z"
        }
    }
]
```

Let's derive a quasi-dockerfile - it looks like it just adds the binary to the container with the libibverbs:

```bash
$ image=602401143452.dkr.ecr.us-west-2.amazonaws.com/eks/aws-efa-k8s-device-plugin:v0.3.3
$ docker history --no-trunc $image  | tac | tr -s ' ' | cut -d " " -f 5- | sed 's,^/bin/sh -c #(nop) ,,g' | sed 's,^/bin/sh -c,RUN,g' | sed 's, && ,\n  & ,g' | sed 's,\s*[0-9]*[\.]*[0-9]*\s*[kMG]*B\s*$,,g' | head -n -1
ADD file:7f69686262e0e0e5415d42ac0371f7d0df0330bc4f0556e5d4b73dd78ceb1197 in /
CMD ["/bin/bash"]
RUN yum update -y
   &&  yum install -y libibverbs
   &&  yum install -y libibverbs-utils
COPY file:0be6d5528203b1645e26be5dff026b6b92b7b0d6050118f1742e03417a965e99 in /usr/bin/efa-k8s-device-plugin
CMD ["efa-k8s-device-plugin"]
```

Let's save it for later.

```bash
docker run --name copier --entrypoint bash -d $image tail -f /dev/null
docker cp copier:/usr/bin/efa-k8s-device-plugin ./efa-k8s-device-plugin
```

From your local machine:

```bash 
scp -i my-key-pem.pem ec2-user@ec2-xx-xx-xxx-xxx.compute-1.amazonaws.com:/home/ec2-user/efa-k8s-device-plugin ./efa-k8s-device-plugin
```

You can look at the binary to see imports - I won't post that online because it might qualify as reverse engineering,
which we don't need to do yet.
