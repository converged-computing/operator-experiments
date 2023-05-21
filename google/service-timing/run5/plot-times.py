import pandas
import seaborn as sns
import matplotlib.pyplot as plt
import json
import os
import re


def read_json(filename):
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content


here = os.path.abspath(os.path.dirname(__file__))


def recursive_find(base, pattern="^(.*[.]json)$"):
    """
    Recursively find json output files
    """
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            if re.search(pattern, filename):
                yield os.path.join(root, filename)


df = pandas.DataFrame(columns=["runtime", "group"])
idx = 0


for filename in recursive_find(os.path.join(here, "data")):
    data = read_json(filename)

    # The tag identifier with flags we used is the directory name
    tag = os.path.basename(os.path.dirname(filename))
    print(f"Found result for {tag}")

    # Don't include first timepoint to pull container to cluster
    times = data["times"][1:]
    for point in times:
        df.loc[idx, :] = [point, tag]
        idx += 1

# Show means by the runtime
mean = df.runtime.mean()
print(f"Mean runtime across runs: {mean}")
means = df.groupby(["group"])["runtime"].mean().sort_values()
print(f"Means for flag groups: {means}")

# Draw a nested boxplot to show time for nslookup to work
plt.figure(figsize=(12, 8))
sns.set(font_scale=0.8)
plt = sns.boxplot(x="group", y="runtime", hue="group", data=df)
plt.set(title="Comparing flux start time with no-dns vs. dns")
plt.set_ylabel("Total flux start hookup time (seconds)", fontsize=16)
plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0)
plt.set(xlabel=None)
plt.set(xticklabels=[])
fig = plt.get_figure()
fig.tight_layout()

fig.savefig("flux-start-times.png")
