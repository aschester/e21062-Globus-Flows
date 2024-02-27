#!/bin/bash

shifter --image=fribdaq/frib-buster:v4.2 --volume="/global/cfs/cdirs/m4386/opt-buster:/usr/opt;/global/cfs/cdirs/m4386/e21062_flows/converted/run$1:/input;/global/cfs/cdirs/m4386/e21062_flows/analyzed:/output;/global/cscratch1/sd/chester/tmpfiles:/tmp:perNodeCache=size=100G" --env-file=/global/homes/c/chester/shifter.env --module=none /global/homes/c/chester/globus_flows/run_compute_analyze.sh $1
$2
