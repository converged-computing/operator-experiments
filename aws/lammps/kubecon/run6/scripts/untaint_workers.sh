#!/bin/bash

# This is the same, but with a hyphen at the end to remove it
for n in $( kubectl get nodes -l flux-operator=true | tail -n +2 | cut -d' ' -f1 ); do
    kubectl taint nodes $n worker=true:NoSchedule-
done 

