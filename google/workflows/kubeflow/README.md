# Testing Kubeflow

We are going to test out KubeFlow, and our goals are to imagine it as a central orchestration
strategy for running lab or HPC workflows on the cloud.

## Usage

### Setup Anthos

> Anthos will be our top level orchestrator, even above Kubernetes

Following instructions [here](https://www.kubeflow.org/docs/started/installing-kubeflow/), 
and then specific instructions for [Google Cloud](https://googlecloudplatform.github.io/kubeflow-gke-docs/docs/deploy/overview/),
first create a cluster on Google Cloud (GKE). After enabling the services, we can install the
Anthos service mesh:

```bash
GOOGLE_PROJECT=myproject
curl --request POST \
  --header "Authorization: Bearer $(gcloud auth print-access-token)" \
  --data '' \
  https://meshconfig.googleapis.com/v1alpha1/projects/${GOOGLE_PROJECT}:initialize
```

This won't create a cluster, but will enable anthos (that will be our controller to do so).
We are going to ignore the next step to set up OAuth login - this would only be necessary
for production deployments. 

### Software Dependencies

So next, I installed the executables I needed using gcloud
from [these instructions](https://googlecloudplatform.github.io/kubeflow-gke-docs/docs/deploy/management-setup/):

```
gcloud components install kubectl kustomize kpt anthoscli beta
gcloud components update
```

### KubeFlow

#### Setup

Get the Kubeflow "blueprints" which I think are just the manifests. I found the kpt download
example had an error, so I used just GitHub (also note that you can look at [kpt here](https://github.com/GoogleContainerTools/kpt)):

```
git clone https://github.com/googlecloudplatform/kubeflow-distribution.git 
cd kubeflow-distribution
git checkout tags/v1.7.0 -b v1.7.0
cd ./management
```

#### Management Cluster

Then deploy the management cluster! We need a few environment variables (update these to your liking):

```bash
MGMT_PROJECT=<the project where you deploy your management cluster>
MGMT_NAME=<name of your management cluster>
LOCATION=<location of your management cluster, use either us-central1 or us-east1>
```

I did:

```bash
export MGMT_PROJECT=$GOOGLE_PROJECT
export MGMT_NAME=kubeflow-mgmt
export LOCATION=us-central1
```

Then use kpt set to set values in the manifests. I think this is comparable to helm -
take a look at this script and you can see we are targeting the directory of manifests
with some variables to fill in.


```bash
$ bash kpt-set.sh
```
```console
[RUNNING] "gcr.io/kpt-fn/apply-setters:v0.1"
[PASS] "gcr.io/kpt-fn/apply-setters:v0.1" in 300ms
  Results:
    [info] data.name: set field value to "kubeflow-mgmt"
    [info] data.gcloud.core.project: set field value to "llnl-flux"
    [info] data.location: set field value to "us-central1"
[RUNNING] "gcr.io/kpt-fn/apply-setters:v0.1"
[PASS] "gcr.io/kpt-fn/apply-setters:v0.1" in 200ms
...
```

This command tells us "setters" and their values in the packages.

```bash
kpt fn eval -i list-setters:v0.1 ./manifests
```

You can check under "manifests" to sanity check the cluster isn't crazy - it has min to max
size of 1 to 3 (with autoscaling) and runs on n1-standard-4, which would be about $60 a day
if you let it run for 24 hours. And now we can create the cluster!

```console
# Create the management cluster
make create-cluster

# Create a kubectl context for the management cluster, it will be named ${MGMT_NAME}:
make create-context

# Grant permission to Config Controller service account:
make grant-owner-permission
```

Note that this management cluster is for orchestrating other things - other clusters
or databases. The documentation says that only one is needed per project. Importantly,
instructions for [debugging are here](https://googlecloudplatform.github.io/kubeflow-gke-docs/docs/deploy/management-setup/#debug). If/when you want to delete:

```bash
$ make delete-cluster
```

I'm not sure why it takes so long to create - I found this a bit annoying.

#### Deploy KubeFlow

Next we can [deploy KubeFlow](https://googlecloudplatform.github.io/kubeflow-gke-docs/docs/deploy/deploy-cli/).
We are already sitting in the cloned repository from the step above in "management" so let's just move around
and run the script:

```
# Change directory from management to the Kubeflow cluster related manifests
cd ../kubeflow

bash ./pull-upstream.sh
```

Note that I stopped here and decided to try kind first. This was taking too long and it
was getting boring.
