#!/bin/bash

# This will install k3s. This requires a base image with cgroups 2 enabled!
# It's also intended for Rocky Linux.

# CHANGE THIS TO SOMETHING DIFFERENT!
secret_token=pancakes-chicken-finger-change-me
username=sochat1_llnl_gov
##

# Bind utils has nslookup to get ip address
dnf update -y 
dnf install -y wget bind-utils

# Instal NFS home
mkdir -p /var/nfs/home
chown nobody:nobody /var/nfs/home

ip_addr=$(hostname -I)

echo "/var/nfs/home *(rw,no_subtree_check,no_root_squash)" >> /etc/exports

firewall-cmd --add-service={nfs,nfs3,mountd,rpc-bind} --permanent
firewall-cmd --reload

systemctl enable --now nfs-server rpcbind

# Hello server, who are you?
name=$(hostname)
echo "Hello I am ${name}"

# I hard coded my home in for now... you'll need to change this!
# Otherwise this will be in root's home
# We likely want an init or similar script to do this!
wget https://raw.githubusercontent.com/k3s-io/k3s/master/k3s-rootless.service
mkdir -p /home/$username/.config/systemd/user
mv ./k3s-rootless.service /home/$username/.config/systemd/user/k3s-rootless.service

### k3s (master node) vs worker
if [[ "${name}" == "k3s-login-001" ]]; then
    
    # We might be able to do this?
    curl -sfL https://get.k3s.io | K3S_TOKEN=${secret_token} sh -

    export KUBECONFIG=/home/$username/.kube/config
    mkdir /home/$username/.kube

    # TODO double check if this config is correct for rootless mode!
    cp /etc/rancher/k3s/k3s.yaml /home/$username/.kube/config

    # Get the kubeconfig to use
    # chmod 600 "$KUBECONFIG"
    chown -R $username /home/$username/.config
    chown -R $username /home/$username/.kube
    echo "export KUBECONFIG=/home/$username/.kube/config" >> /home/$username/.profile

    # Reload!
    systemctl --user daemon-reload
    systemctl --user enable --now k3s-rootless

else
    # Janky sleep to try to make it happen with some delay...
    sleep 60
    login_node=$(nslookup k3s-compute-a-001 | grep Address |  sed -n '2 p' |  sed 's/Address: //g')
    curl -sfL https://get.k3s.io | K3S_URL=https://${login_node}:6443 K3S_TOKEN=${secret_token} sh -
fi

# if you need to debug
# journalctl --user -f -u k3s-rootless

# Now you can get nodes:
# kubectl get nodes
