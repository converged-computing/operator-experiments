#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
sleep $BATCH_TASK_INDEX

# Note that for this family / image, we are root (do not need sudo)
yum update -y && yum install -y cmake gcc tuned ethtool python3

# Ensure a python3 executable is found, if does not exist
which python3 || (ln -s $(which python) /usr/bin/python3)

# This ONLY works on the hpc-* image family images
google_mpi_tuning --nosmt
# google_install_mpi --intel_mpi
google_install_intelmpi --impi_2021
source /opt/intel/mpi/latest/env/vars.sh
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/intel/mpi/latest/lib:/opt/intel/mpi/latest/lib/release
export PATH=/opt/intel/mpi/latest/bin:$PATH
outdir=/mnt/share/data/netmark-experiment-size-32
mkdir -p $outdir
find /opt/intel -name mpicc

# Only have index 0 compile
if [ $BATCH_TASK_INDEX = 0 ]; then
  cd /mnt/share/netmark
  ls
  # And only compile if the executable does not exist!   
  # Makefile content plus adding include directories
  if [[ ! -f "netmark.x" ]]; then
      mpicc -std=c99 -lmpi -lmpifort -O3 netmark.c -DTRACE -I/opt/intel/mpi/latest/include -I/opt/intel/mpi/2021.8.0/include -L/opt/intel/mpi/2021.8.0/lib/release -L/opt/intel/mpi/2021.8.0/lib -o netmark.x 
   fi
fi