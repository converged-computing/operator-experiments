## Results

We have provided  a [process_lammps.py](process_lammps.py) script you can
use against the output data directory (and output files) to visualize the results.

```bash
$ python -m venv env 
$ source env/bin/activate
$ pip install -r requirements.txt
```

Next, run the script targeting the data directory here, the mpi operator results
that are from [here](../mpi-operator-comparison) and the metadata file.

```bash
$ python process_lammps.py ./data --meta data/k8s-size-64-hpc6a.48xlarge/meta.json --mpi-operator mpi_operator_results.json
```

And then plot the json results:

```bash
$ python plot_results.py
```

# TODO

- plot creation / down times (minus the job running time) and make distribution
- convert to violin plots
- side by side for flux runtime and mpi operator runtime
- show size 64 too, not run with mpi-operator (maybe they have insights) full flux runtime and lammps
- we are optimistic that the medians are going down

LAMMPS mpi containers are not optimized for that hardware. 
These are the first runs, they are close to the MPI oeprator - there are huge amounts
of features / runtime capabilties we are enablign with this, and we still can
further test.

64 note more suseptible to cluster variability? 

