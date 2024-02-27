#!/bin/sh

gce=$HOME/globus_flows/globus_compute_venv/bin/globus-compute-endpoint
endpoints=("frib-analysis-singlenode" "frib-analysis-multinode")

for ep in ${endpoints[@]}
do
    echo "----- Setup $ep -----"
    $gce configure $ep
    cp config-$ep.yaml ~/.globus_compute/$ep/config.yaml
    $gce start $ep
done
