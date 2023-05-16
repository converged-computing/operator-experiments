import pandas
import seaborn as sns
import json
import os
import re


def read_json(filename):
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content


here = os.path.abspath(os.path.dirname(__file__))


def recursive_find(base, pattern="^(nslookup.*[.]json)$"):
    """
    Recursively find json output files
    """
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            if re.search(pattern, filename):
                yield os.path.join(root, filename)


df = pandas.DataFrame(columns=["runtime", "flags"])
idx = 0
for filename in recursive_find(os.path.join(here, "data", "nslookup")):
    data = read_json(filename)

    # The tag identifier with flags we used is the directory name
    tag = os.path.basename(os.path.dirname(filename))
    print(f"Found result for {tag}")

    # Don't include first timepoint to pull container to cluster
    times = data["times"][1:]
    for point in times:
        df.loc[idx, :] = [point, tag]
        idx += 1

df["runtime"] = df["runtime"].astype("float64")

# Show means by the runtime
mean = df.runtime.mean()
print(f"Mean runtime across runs: {mean}")
means = df.groupby(["flags"])["runtime"].mean().sort_values()
print(f"Means for flag groups: {means}")

# Draw a nested boxplot to show bills by day and time
sns.set(font_scale=0.8)
plt = sns.violinplot(x="flags", y="runtime", hue="flags", data=df, whis=[5, 95])
plt.set(title="Comparing nslookup of the broker hostname across different GKE flags")
plt.tick_params(axis="x", rotation=20)
plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0)
plt.set(xlabel=None)
plt.set(xticklabels=[])
fig = plt.get_figure()
fig.tight_layout()

fig.savefig("nslookup-times.png")
