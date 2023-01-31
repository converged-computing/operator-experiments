# Fixed EFA

The update to eksctl broke being able to create the efa pods [see this issue](https://github.com/weaveworks/eksctl/issues/6222).
So this experiment created the cluster, and grabbed the previous config as [efa-device-plugin.yaml](efa-device-plugin.yaml)
to create the containers and allow root. I had to clone eksctl, replace the plugin file with the one here, rebuild,
and use that binary. So this run includes all 4 cluster sizes, with efa, and more detailed flux timings.

**Analysis and final results TBA**
