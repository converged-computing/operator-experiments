import pandas
import seaborn as sns
import json
import sys
import os


def read_json(filename):
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content


here = os.path.dirname(os.path.abspath(__file__))
workers = read_json(os.path.join(here, "no-service", "workers.json"))
leaders_no_service = read_json(os.path.join(here, "no-service", "leaders.json"))
leaders_service = read_json(os.path.join(here, "service", "leaders.json"))

# Combine into data frames
df = pandas.DataFrame(columns=["stage", "type", "time", "service"])

# There is a lot of data! Only save what we need:
# We don't need to look at the workers, the leader is what matters
# 'init->quorum': RANK 0: reflects any delay in running rc1
# 'quorum->run': RANK 0: this would be the time it takes to network?
# 'run->cleanup': RANK 0: this would be the runtime of lammps

# Manually add them!
idx = 0
for run, meta in leaders_no_service.items():
    for stage, time in meta.items():
        df.loc[idx, :] = [stage, "leader", time, "no-service"]
        idx += 1
for run, meta in leaders_service.items():
    for stage, time in meta.items():
        df.loc[idx, :] = [stage, "leader", time, "service"]
        idx += 1

sns.set(font_scale=0.8)

# Plot each of the times
for stage in df.stage.unique():
    subset = df[df.stage == stage]
    plt = sns.histplot(data=subset, x="time", bins=70, kde=True, hue="service")
    plt.set(title=f"Time for LAMMPS for stage {stage}")
    handles, labels = plt.get_legend_handles_labels()
    fig = plt.get_figure()
    stage = stage.replace("->", "-to-")
    fig.savefig(f"lammps-hist-stage-{stage}.png")
    plt.clear()

# df.to_csv("leaders.csv")
# Don't plot workers for now
sys.exit()

# Add the workers to the data
worker_count = 0
total = len(workers)
for run, meta in workers.items():
    worker_count += 1
    print(f"{worker_count} of {total}", end="\r")
    for stage, time in meta.items():
        df.loc[idx, :] = [stage, "worker", time]
        idx += 1

# df.to_csv("leaders-and-workers.csv")

# Plot each of the times
for stage in df.stage.unique():
    subset = df[df.stage == stage]
    #w = subset[subset.type == "worker"]
    #l = subset[subset.type == "leader"]
    plt = sns.displot(data=subset, x="time", hue="type")
    #sns.distplot(w['time'], hist=False, rug=True)
    #sns.distplot(l['time'], hist=False, rug=True)
    plt.set(title=f"Time for LAMMPS for stage {stage} between leaders and workers")
    stage = stage.replace("->", "-to-")
    plt.savefig(f"lammps-hist-leaders-vs-workers-stage-{stage}.png")

