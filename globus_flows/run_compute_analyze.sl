#!/bin/bash

##
# @file run_compute_analyze.sl
# @brief Submission script for running Liddick group betasort.
# @param 1 Run number.
# @param 2 Number of run segments. A value of 0 (zero) will select only the
#          first segment.
#
# Usage: sbatch run_compute_analyze.sl <run> <segments>
#

#SBATCH -A m4386
#SBATCH --licenses=scratch,cfs
#SBATCH -q debug
#SBATCH -C cpu
#SBATCH -n 1
#SBATCH -c 1
#SBATCH --mem=40G

shifter --image=fribdaq/frib-buster:v4.2 --volume="$CFS/m4386/opt-buster:/usr/opt;$CFS/m4386/e21062_flows/converted/run$1:/input;$CFS/m4386/chester/flows_testing:/output;/global/cscratch1/sd/chester/tmpfiles:/tmp:perNodeCache=size=100G" --env-file=$HOME/shifter.env --module=none $HOME/globus_flows/run_compute_analyze.sh $1 $2
