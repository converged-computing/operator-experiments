#!/bin/bash
export PATH=/opt/intel/mpi/latest/bin:$PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/intel/mpi/latest/lib:/opt/intel/mpi/latest/lib/release
source /opt/intel/mpi/latest/env/vars.sh

# Ensure we have the wrapper template and it's correctly populated
wrapper=/mnt/share/data/netmark-experiment-size-100/netmark_wrapper.sh
cat ${wrapper}
chmod +x ${wrapper}

echo "Batch hosts file is $BATCH_HOSTS_FILE"
cat $BATCH_HOSTS_FILE

if [ $BATCH_TASK_INDEX = 0 ]; then
  cd /mnt/share/data/netmark-experiment-size-100
  ls
  echo "mpirun -n 100 -ppn 1 -f BATCH_HOSTS_FILE ${wrapper}"
  mpirun -n 100 -ppn 1 -f $BATCH_HOSTS_FILE ${wrapper}
else
  # Since we cannot set a barrier, this keeps the instances running
  while [ ! -f "/mnt/share/data/netmark-experiment-size-100/RTT.csv" ]; do 
    sleep 30;
  done
  echo "RTT.csv exists, netmark is done."
fi