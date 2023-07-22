import pandas
import seaborn as sns
import json
import sys
import os

# Default to PWD or custom directory for data
if len(sys.argv) < 2:
    here = os.path.dirname(os.path.abspath(__file__))
else:
    here = os.path.abspath(sys.argv[1])
print(f'Running assuming data directory is in {here}')

def read_json(filename):
    with open(filename, "r") as fd:
        content = json.loads(fd.read())
    return content

no_services = read_json(os.path.join(here, "data", "lammps", "lammps-no-services.json"))
with_services = read_json(
    os.path.join(here, "data", "lammps", "lammps-with-services.json")
)

# Combine into data frames
df = pandas.DataFrame(columns=["timeout", "runtime", "services"])

# Manually add them! We are lazy
idx = 0
for seconds, points in no_services["times"].items():
    if seconds == "no-timeout-set":
        seconds = "none"
    for point in points:
        df.loc[idx, :] = [seconds, point, "no"]
        idx += 1

for seconds, points in with_services["times"].items():
    if seconds == "no-timeout-set":
        seconds = "none"
    for point in points:
        df.loc[idx, :] = [seconds, point, "yes"]
        idx += 1

# Draw a nested boxplot to show bills by day and time
sns.set(font_scale=0.8)

plt = sns.boxplot(x="timeout", y="runtime", hue="services", palette=["m", "g"], data=df)
plt.set(
    title="Runtime for LAMMPS with or without unrelated services, across zeromq connect timeouts"
)
handles, labels = plt.get_legend_handles_labels()
fig = plt.get_figure()

fig.savefig("lammps-times.png")
