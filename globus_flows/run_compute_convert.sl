#!/bin/bash

#SBATCH -A m4386
#SBATCH --licenses=scratch,cfs
#SBATCH -q debug
#SBATCH -C cpu
#SBATCH -n 1
#SBATCH -c 1

shifter --image=fribdaq/frib-buster:v4.2 --volume="$CFS/m4386/opt-buster:/usr/opt;$CFS/m4386/e21062_flows/fitted/run$1:/input;$CFS/m4386/chester/flows_testing:/output;/global/cscratch1/sd/chester/tmpfiles:/tmp:perNodeCache=size=100G" --env-file=$HOME/shifter.env --module=none $HOME/globus_flows/run_compute_convert.sh $1 $2
