# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# 1 manager node + 1 login node + 126 compute nodes
manager_machine_type = "c2d-standard-112"
manager_name_prefix  = "gffw"
manager_scopes       = [ "cloud-platform" ]

login_node_specs = [
    {
        name_prefix  = "gffw-login"
        machine_arch = "x86-64"
        machine_type = "c2d-standard-112"
        instances    = 1
        properties   = []
        boot_script  = "install_lammps.sh"
    },
]
login_scopes = [ "cloud-platform" ]

compute_node_specs = [
    {
        name_prefix  = "gffw-compute-a"
        machine_arch = "x86-64"
        machine_type = "c2d-standard-112"
        gpu_type     = null
        gpu_count    = 0
        compact      = true
        instances    = 126
        properties   = []
        boot_script  = "install_lammps.sh"
    },
]
compute_scopes = [ "cloud-platform" ]
