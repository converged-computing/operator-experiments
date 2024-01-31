#!/bin/bash
# Note that for this family / image, we are root (do not need sudo)
yum update -y && yum install -y hwloc

outdir=/mnt/share/lscpu/n2d-standard-4
mkdir -p $outdir
cd $outdir
echo $PWD
lstopo-no-graphics > topology.txt
lstopo-no-graphics -.ascii > topology-ascii.txt           
lscpu > lscpu.txt
hwloc-ls machine.xml
ls