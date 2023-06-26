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

Note this is how to get info for the plugin I think?

```
/opt/amazon/efa/bin/fi_info -p efa
```
