import pandas
import matplotlib.pylab as pylab
import seaborn as sns
import json
import sys
import os

# Times are here
here = os.path.dirname(os.path.abspath(__file__))
times_file = os.path.join(here, "times.log")

# Output images
outdir = os.path.join(here, "img")
if not os.path.exists(outdir):
    os.makedirs(outdir)

df = pandas.read_csv(times_file)
df.columns = ["metric", "seconds", "nodes"]

# Draw a nested boxplot to show bills by day and time
sns.set(font_scale=0.8)

# Make a plot for each metric
metrics = df.metric.unique()
for metric in metrics:
    print(f"Plotting OSU Benchmark {metric}")
    subset = df[df.metric == metric]
    plt = sns.scatterplot(x="nodes", y="seconds", hue="nodes", data=subset, palette="muted")
    # When we have > 1 point
    # plt = sns.boxplot(x="nodes", y="seconds", hue="nodes", palette=["m", "g"], data=subset)
    plt.set(title=f"{metric} time (seconds) to run across c2d-standard-2 sizes")
    handles, labels = plt.get_legend_handles_labels()
    fig = plt.get_figure()
    fig.savefig(os.path.join(outdir, f"osu_benchmark_{metric}.png"))
    pylab.close()
