#!/bin/bash

# This boot script will install lammps on all nodes
dnf install nfs-utils -y

mkdir -p /var/nfs/home
chown nobody:nobody /var/nfs/home

ip_addr=$(hostname -I)

echo "/var/nfs/home *(rw,no_subtree_check,no_root_squash)" >> /etc/exports

firewall-cmd --add-service={nfs,nfs3,mountd,rpc-bind} --permanent
firewall-cmd --reload

systemctl enable --now nfs-server rpcbind

# Install time for timed commands
dnf update -y && dnf install -y time cmake openmpi clang git-clang-format
ldconfig

# Needed for ffmpeg
dnf install -y https://download1.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm
dnf install -y https://download1.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-8.noarch.rpm
dnf install -y ffmpeg

# install laamps
git clone --depth 1 --branch stable_29Sep2021_update2 https://github.com/lammps/lammps.git /opt/lammps
cd /opt/lammps
mkdir build
cd build

# The cmake prefix path is needed otherwise openmpi is not found
cmake ../cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -D PKG_REAXFF=yes -D BUILD_MPI=yes -D PKG_OPT=yes -D FFT=FFTW3 -DCMAKE_PREFIX_PATH=/usr/lib64/openmpi
make
make install

# Run from a node:
# cd /opt/lammps/examples/reaxff/HNS
# flux run -n 1 lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
