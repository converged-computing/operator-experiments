## Results

We have provided  a [process_lammps.py](process_lammps.py) script you can
use against the output data directory (and output files) to visualize the results.

```bash
$ python -m venv env 
$ source env/bin/activate
$ pip install -r requirements.txt
```

Next, run the script targeting the data directory here:

```bash
$ python process_lammps.py ./data
```

And then plot the json results:

```bash
$ python plot_results.py
```
