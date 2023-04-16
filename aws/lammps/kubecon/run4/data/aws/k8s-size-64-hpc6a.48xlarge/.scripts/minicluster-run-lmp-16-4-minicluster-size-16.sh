#!/bin/bash

# This is a template that will be populated with variables by Flux-Cloud
# It used to be a script proper with getopt, but in practice this was
# erroneous on different operating systems.

# Include shared helper scripts
# Colors
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[0;33m'
blue='\033[0;34m'
magenta='\033[0;35m'
cyan='\033[0;36m'
clear='\033[0m'

function print_red() {
    echo -e "${red}$@${clear}"
}
function print_yellow() {
    echo -e "${yellow}$@${clear}"
}
function print_green() {
    echo -e "${green}$@${clear}"
}
function print_blue() {
    echo -e "${blue}$@${clear}"
}
function print_magenta() {
    echo -e "${magenta}$@${clear}"
}
function print_cyan() {
    echo -e "${cyan}$@${clear}"
}

function is_installed () {
    # Determine if a command is available for use!
    cmd="${1}"
    if command -v $cmd >/dev/null; then
        echo "$cmd is installed"
    else
        echo "$cmd could not be found"
        exit 1
    fi
}

function install_operator() {
    # Shared function to install the operator from a specific repository branch and cleanup
    script_dir=${1}
    repository=${2}
    branch=${3}
    tmpfile="${script_dir}/flux-operator.yaml"
    run_echo wget -O $tmpfile https://raw.githubusercontent.com/${repository}/${branch}/examples/dist/flux-operator.yaml
    kubectl apply -f $tmpfile
}

function save_common_metadata() {
    # Save common versions across clouds for kubectl and the cluster nodes
    SCRIPT_DIR="${1}"
    SIZE="${2}"

    run_echo_save "${SCRIPT_DIR}/kubectl-version.yaml" kubectl version --output=yaml

    # Show nodes and save metadata to script directory
    run_echo kubectl get nodes
    run_echo_save "${SCRIPT_DIR}/nodes-size-${SIZE}.json" kubectl get nodes -o json
    run_echo_save "${SCRIPT_DIR}/nodes-size-${SIZE}.txt" kubectl describe nodes
}



function run_echo() {
    # Show the user the command then run it
    echo
    print_green "$@"
    retry $@
}

function run_echo_save() {
    echo
    save_to="${1}"
    shift
    print_green "$@ > ${save_to}"
    $@ > ${save_to}
}

function run_echo_allow_fail() {
    echo
    print_green "$@"
    $@ || true
}

function retry() {
    # Retry an unsuccessful user command, per request
    while true
    do
        $@
        retval=$?
        if [[ "${retval}" == "0" ]]; then
            return
        fi
        print_blue "That command was not successful. Do you want to try again? 🤔️"
        read -p " (yes/no) " answer
        # Exit with non-zero response so we know to stop in script.
        case ${answer} in
	       yes ) continue;;
           no ) echo exiting...;
	            exit 1;;
	       * )  echo invalid response;
		        exit 1;;
        esac
    done
}


function prompt() {
    # Prompt the user with a yes/no command to continue or exit
    print_blue "$@ 🤔️"
    read -p " (yes/no) " answer
    case ${answer} in
	    yes ) echo ok, we will proceed;;
        no ) echo exiting...;
	         exit 1;;
	    * )  echo invalid response;
		     exit 1;;
    esac
}


function with_exponential_backoff {
    # Run with exponential backoff - assume containers take a while to pull
    local max_attempts=100
    local timeout=1
    local attempt=0
    local exitcode=0

    while [[ $attempt < $max_attempts ]]; do
      "$@"
      exitcode=$?

      if [[ $exitcode == 0 ]]; then
        break
      fi

      echo "Failure! Retrying in $timeout.." 1>&2
      sleep $timeout
      attempt=$(( attempt + 1 ))
      timeout=$(( timeout * 2 ))
    done

    if [[ $exitCode != 0 ]]; then
      echo "You've failed me for the last time! ($@)" 1>&2
    fi
    return $exitcode
}

NAMESPACE="flux-operator"
CRD="/home/vanessa/Desktop/Code/flux/experiments/aws/lammps/kubecon/run4/data/aws/k8s-size-64-hpc6a.48xlarge/.scripts/minicluster-size-16.yaml"
JOB="lammps"
LOGFILE="/home/vanessa/Desktop/Code/flux/experiments/aws/lammps/kubecon/run4/data/aws/k8s-size-64-hpc6a.48xlarge/lmp-16-4-minicluster-size-16/log.out"

print_magenta "  apply : ${CRD}"
print_magenta "    job : ${JOB}"
print_magenta "logfile : ${LOGFILE}"

is_installed kubectl

# Ensure we wait for the space to be cleaned up
echo
podsCleaned="false"
print_blue "Waiting for previous MiniCluster to be cleaned up..."
while [[ "${podsCleaned}" == "false" ]]; do
    echo -n "."
    sleep 2
    state=$(kubectl get pods --namespace ${NAMESPACE} 2>&1)
    lines=$(echo $state | wc -l)
    if [[ "${lines}" == "1" ]] && [[ "${state}" == *"No resources found in"* ]]; then
        echo
        print_green "🌀️ Previous pods are cleaned up."
        podsCleaned="true"
        break
    fi
done

# Create the namespace (ok if already exists)
run_echo_allow_fail kubectl create namespace ${NAMESPACE}

# Apply the job, get pods
run_echo kubectl apply -f ${CRD}
run_echo kubectl get -n ${NAMESPACE} pods

# continue until we find the index-0 pod
brokerPrefix="${JOB}-0"
brokerReady="false"

echo
print_blue "Waiting for broker pod with prefix ${brokerPrefix} to be created..."
while [[ "${brokerReady}" == "false" ]]; do
    echo -n "."
    sleep 2
    for pod in $(kubectl get pods --selector=job-name=${JOB} --namespace ${NAMESPACE} --output=jsonpath='{.items[*].metadata.name}'); do
        if [[ "${pod}" == ${brokerPrefix}* ]]; then
            echo
            print_green "🌀️ Broker pod is created."
            brokerReady="true"
            break
        fi
    done
done

# Now broker pod needs to be running
echo
print_blue "Waiting for broker pod with prefix ${brokerPrefix} to be running..."
brokerReady="false"
while [[ "${brokerReady}" == "false" ]]; do
    echo -n "."

    # TODO - we likely want to check for running OR completed, it's rare but sometimes they can complete too fast.
    for pod in $(kubectl get pods --namespace ${NAMESPACE} --field-selector=status.phase=Running --output=jsonpath='{.items[*].metadata.name}'); do
        if [[ "${pod}" == ${brokerPrefix}* ]]; then
            echo
            print_green "🌀️ Broker pod is running."
            brokerReady="true"
            break
        fi
    done
done

# Get the name of the pods
pods=($(kubectl get pods --selector=job-name=${JOB} --namespace ${NAMESPACE} --output=jsonpath='{.items[*].metadata.name}'))
brokerpod=${pods[0]}

# This will hang like this until the job finishes running
echo
print_green "kubectl -n ${NAMESPACE} logs ${brokerpod} -f > ${LOGFILE}"
kubectl -n ${NAMESPACE} logs ${brokerpod} -f > ${LOGFILE}

for exitcode in $(kubectl get -n ${NAMESPACE} pod --selector=job-name=${JOB} --output=jsonpath={.items...containerStatuses..state.terminated.exitCode}); do
    if [[ "${exitcode}" != "0" ]]; then
       echo "Container in ${JOB} had nonzero exit code"
    fi
done

run_echo kubectl delete -f ${CRD}