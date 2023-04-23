#!/bin/bash

# This boot script will install lammps on all nodes

# Install time for timed commands
sudo dnf update -y && sudo dnf install -y time cmake openmpi clang git-clang-format
sudo ldconfig

# Needed for ffmpeg
sudo dnf install -y https://download1.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm
sudo dnf install -y https://download1.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-8.noarch.rpm
sudo dnf install -y ffmpeg

# install laamps
sudo git clone --depth 1 --branch stable_29Sep2021_update2 https://github.com/lammps/lammps.git /opt/lammps
cd /opt/lammps
sudo mkdir build
cd build

# The cmake prefix path is needed otherwise openmpi is not found
sudo cmake ../cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -D PKG_REAXFF=yes -D BUILD_MPI=yes -D PKG_OPT=yes -D FFT=FFTW3 -DCMAKE_PREFIX_PATH=/usr/lib64/openmpi
sudo make
sudo make install

# Run from a node:
# cd /opt/lammps/examples/reaxff/HNS
# flux run -n 1 lmp -v x 1 -v y 1 -v z 1 -in in.reaxc.hns -nocite
