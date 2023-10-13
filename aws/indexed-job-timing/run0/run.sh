#!/bin/bash

size="${1}"

echo "Preparing to run experiments for size ${size}"
for i in {0..10}; do
  echo "Running experiment ${i} for size-${size} test"
  python pod-events.py experiments/size-${size} --size ${size} --idx=${i}
done
