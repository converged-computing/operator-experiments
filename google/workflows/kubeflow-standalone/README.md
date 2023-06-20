# Testing Kubeflow 

> This is a less complex setup than using Anthos, etc.

I was a bit scared off by the complexity of [this setup](../kubeflow).
I think it would be great for a hard, production cluster, but it's simply too much
to develop or try something out. So I'm hoping to try [this simpler setup](https://www.kubeflow.org/docs/components/pipelines/v1/installation/standalone-deployment/). It would be hard to develop for a tool
that requires so much manual command-running and waiting in the long term.

## Usage

### Create Cluster

```bash
GOOGLE_PROJECT=myproject
CLUSTER_NAME="kubeflow-pipelines-standalone"

gcloud container clusters create $CLUSTER_NAME  \
     --zone "us-central1-a" \
     --machine-type "e2-standard-2"  \
     --scopes "cloud-platform" \
     --project $GOOGLE_PROJECT
```

Next (when your cluster is ready and healthhy!) [deploy pipelines](https://www.kubeflow.org/docs/components/pipelines/v1/installation/standalone-deployment/#deploying-kubeflow-pipelines)

```bash
export PIPELINE_VERSION=1.8.5
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=$PIPELINE_VERSION"
```

Here is how to get the public URL for pipelines:

```
kubectl describe configmap inverse-proxy-config -n kubeflow | grep googleusercontent.com
```
```console
4ad924b8db1028a2-dot-us-central1.pipelines.googleusercontent.com
```

I think you can do stuff there, but I'm instead trying to do this programmatically so I better
understand how it works.

### Install SDK

We will need the [KubeFlow Pipelines SDK](https://www.kubeflow.org/docs/components/pipelines/v1/sdk/install-sdk/).

```bash
python -m venv env
source env/bin/activate
pip install kfp --upgrade
```

This gives us these two things we will use next:

```
# 
kfp

# Turn a Python script into a .tar.gz to give to KubeFlow
dsl-compile
```

### Demo Pipeline

Following the instructions [here](https://www.kubeflow.org/docs/components/pipelines/v1/tutorials/api-pipelines/)
let's download an example pipeline.

```bash
PIPELINE_URL=https://raw.githubusercontent.com/kubeflow/pipelines/master/samples/core/sequential/sequential.py
PIPELINE_FILE=${PIPELINE_URL##*/}
PIPELINE_NAME=${PIPELINE_FILE%.*}

wget -O ${PIPELINE_FILE} ${PIPELINE_URL}
dsl-compile --py ${PIPELINE_FILE} --output ${PIPELINE_NAME}.tar.gz
```
I'm saving [sequential.py](sequential.py) here for provenance. This is what Paula
was talking about when she said compiler - the imports here are from the library [kfp]()
and they are for a dsl and the compiler:

```python
from kfp import dsl, compiler
```

We can compile as follows:

```
dsl-compile --py ${PIPELINE_FILE} --output ${PIPELINE_NAME}.tar.gz
```

We made a thing!

```
ls
env README.md  sequential.py  sequential.tar.gz
```

If we look inside - it's literally just a YAML file! I promise.
Next, port forward the ml-pipeline service:

```
SVC_PORT=$(kubectl -n kubeflow get svc/ml-pipeline -o json | jq ".spec.ports[0].port")
kubectl port-forward -n kubeflow svc/ml-pipeline ${SVC_PORT}:8888
```

In a different terminal, let's use the RESTFul API to give the pipeline to our interface.
In a different terminal:

```bash
PIPELINE_URL=https://raw.githubusercontent.com/kubeflow/pipelines/master/samples/core/sequential/sequential.py
PIPELINE_FILE=${PIPELINE_URL##*/}
PIPELINE_NAME=${PIPELINE_FILE%.*}
SVC=localhost:8888
PIPELINE_ID=$(curl -F "uploadfile=@${PIPELINE_NAME}.tar.gz" ${SVC}/apis/v1beta1/pipelines/upload | jq -r .id)
```
This will give you a pipeline id:

```bash
$ echo $PIPELINE_ID 
aced0f76-592b-4366-889c-a79395725d52
```

And we can get the status like this:

```bash
curl ${SVC}/apis/v1beta1/pipelines/${PIPELINE_ID} | jq
```
```console
{
  "id": "aced0f76-592b-4366-889c-a79395725d52",
  "created_at": "2023-06-19T23:30:22Z",
  "name": "sequential.tar.gz",
  "parameters": [
    {
      "name": "url",
      "value": "gs://ml-pipeline/sample-data/shakespeare/shakespeare1.txt"
    }
  ],
  "default_version": {
    "id": "aced0f76-592b-4366-889c-a79395725d52",
    "name": "sequential.tar.gz",
    "created_at": "2023-06-19T23:30:22Z",
    "parameters": [
      {
        "name": "url",
        "value": "gs://ml-pipeline/sample-data/shakespeare/shakespeare1.txt"
      }
    ],
    "resource_references": [
      {
        "key": {
          "type": "PIPELINE",
          "id": "aced0f76-592b-4366-889c-a79395725d52"
        },
        "relationship": "OWNER"
      }
    ]
  }
}
```
And note you should also see it in the web UI! You can also trigger a run via the
same API:

```
RUN_ID=$((
curl -H "Content-Type: application/json" -X POST ${SVC}/apis/v1beta1/runs \
-d @- << EOF
{
   "name":"${PIPELINE_NAME}_run",
   "pipeline_spec":{
      "pipeline_id":"${PIPELINE_ID}"
   }
}
EOF
) | jq -r .run.id)
```
```console
$ echo $RUN_ID
8d6a8bba-3785-4c14-8ba7-4938df26ae8c
```

And get the result:

```bash
curl ${SVC}/apis/v1beta1/runs/${RUN_ID} | jq
```
And this can also be seen in the web UI. It's really quite cool! 

### YAML Summary

A summary of the yaml
that was in standalone.tar.gz is below, so we can further inspect:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: sequential-pipeline-
  annotations: {pipelines.kubeflow.org/kfp_sdk_version: 1.8.22, pipelines.kubeflow.org/pipeline_compilation_time: '2023-06-19T17:24:02.669676',
    pipelines.kubeflow.org/pipeline_spec: '{"description": "A pipeline with two sequential
      steps.", "inputs": [{"default": "gs://ml-pipeline/sample-data/shakespeare/shakespeare1.txt",
      "name": "url", "optional": true}], "name": "sequential-pipeline"}'}
  labels: {pipelines.kubeflow.org/kfp_sdk_version: 1.8.22}
spec:
  entrypoint: sequential-pipeline
  templates:
  - name: echo
    container:
      args: [echo "$0", '{{inputs.parameters.gcs-download-data}}']
      command: [sh, -c]
      image: library/bash:4.4.23
    inputs:
      parameters:
      - {name: gcs-download-data}
    metadata:
      labels:
        pipelines.kubeflow.org/kfp_sdk_version: 1.8.22
        pipelines.kubeflow.org/pipeline-sdk-type: kfp
        pipelines.kubeflow.org/enable_caching: "true"
  - name: gcs-download
    container:
      args: [gsutil cat $0 | tee $1, '{{inputs.parameters.url}}', /tmp/results.txt]
      command: [sh, -c]
      image: google/cloud-sdk:279.0.0
    inputs:
      parameters:
      - {name: url}
    outputs:
      parameters:
      - name: gcs-download-data
        valueFrom: {path: /tmp/results.txt}
      artifacts:
      - {name: gcs-download-data, path: /tmp/results.txt}
    metadata:
      labels:
        pipelines.kubeflow.org/kfp_sdk_version: 1.8.22
        pipelines.kubeflow.org/pipeline-sdk-type: kfp
        pipelines.kubeflow.org/enable_caching: "true"
  - name: sequential-pipeline
    inputs:
      parameters:
      - {name: url}
    dag:
      tasks:
      - name: echo
        template: echo
        dependencies: [gcs-download]
        arguments:
          parameters:
          - {name: gcs-download-data, value: '{{tasks.gcs-download.outputs.parameters.gcs-download-data}}'}
      - name: gcs-download
        template: gcs-download
        arguments:
          parameters:
          - {name: url, value: '{{inputs.parameters.url}}'}
  arguments:
    parameters:
    - {name: url, value: 'gs://ml-pipeline/sample-data/shakespeare/shakespeare1.txt'}
  serviceAccountName: pipeline-runner
```

### Clean Up

When you are done:

```bash
$ gcloud container clusters delete $CLUSTER_NAME
```

### Next Steps

This would work well for ML workloads I think - that seems to be the target audience and
design. However, we are interested in extending this. Our next task is to understand how we could implement some kind of custom executor, meaning beyond just using a set of containers / tasks in this setup.
So far I've found that you can write [custom components](https://www.kubeflow.org/docs/components/pipelines/v1/sdk/component-development/) that are scoped to individual containers. This might work if we could
have a component that knows how to burst and monitor to a specific other cluster.


