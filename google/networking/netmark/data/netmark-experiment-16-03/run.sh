#!/bin/bash
export PATH=/opt/intel/mpi/latest/bin:$PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/intel/mpi/latest/lib:/opt/intel/mpi/latest/lib/release
source /opt/intel/mpi/latest/env/vars.sh

# Ensure we have the wrapper template and it's correctly populated
wrapper=/mnt/share/data/netmark-experiment-16-03/netmark_wrapper.sh
cat ${wrapper}
chmod +x ${wrapper}

if [ $BATCH_TASK_INDEX = 0 ]; then
  cd /mnt/share/data/netmark-experiment-16-03
  ls
  mpirun -n 8 -ppn 1 -f $BATCH_HOSTS_FILE ${wrapper}
fi