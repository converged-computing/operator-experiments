# Processing Small Runs on size 8 cluster

Process the data (from this directory) do:

```bash
$ python process.py .
```

And then plot results

```bash
pip install pandas seaborn matplotlib
```

```bash
mkdir -p img
python plot_results.py ./results.json
```