#!/bin/bash

for n in $( kubectl get nodes -l flux-operator=true | tail -n +2 | cut -d' ' -f1 ); do
    kubectl taint nodes $n worker=true:NoSchedule
done 

