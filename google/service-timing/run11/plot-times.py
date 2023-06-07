import pandas
import seaborn as sns
import json
import os


def read_json(filename):
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content


here = os.path.dirname(os.path.abspath(__file__))
# workers = read_json(os.path.join(here, "workers.json"))
leaders = read_json(os.path.join(here, "leaders.json"))

# Combine into data frames
df = pandas.DataFrame(columns=["stage", "type", "time"])

# There is a lot of data! Only save what we need:
# We don't need to look at the workers, the leader is what matters
# 'init->quorum': RANK 0: reflects any delay in running rc1
# 'quorum->run': RANK 0: this would be the time it takes to network?
# 'run->cleanup': RANK 0: this would be the runtime of lammps

# Manually add them!
idx = 0
for run, meta in leaders.items():
    for stage, time in meta.items():
        df.loc[idx, :] = [stage, "leader", time]
        idx += 1

sns.set(font_scale=0.8)

# Plot each of the times
for stage in df.stage.unique():
    subset = df[df.stage == stage]
    plt = sns.histplot(data=subset, x="time", bins=70, kde=True)
    plt.set(title=f"Time for LAMMPS for stage {stage}")
    handles, labels = plt.get_legend_handles_labels()
    fig = plt.get_figure()
    stage = stage.replace("->", "-to-")
    fig.savefig(f"lammps-hist-stage-{stage}.png")
    plt.clear()

df.to_csv("leaders.csv")
