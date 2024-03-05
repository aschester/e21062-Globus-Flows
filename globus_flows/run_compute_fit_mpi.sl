#!/bin/bash

##
# @file run_compute_fit_mpi.sl
# @brief Submission script for running MPI trace fitting.
# @param 1 Run number.
# @param 2 Segment number.
#
# Usage: sbatch run_compute_fit_mpi.sl <run> <segment>
#

#SBATCH -A m4386
#SBATCH --licenses=scratch,cfs
#SBATCH -q debug
#SBATCH -C cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 128

shifter --image=fribdaq/frib-buster:v4.2 --volume="$CFS/m4386/opt-buster:/usr/opt;$CFS/m4386/e21062_flows/rawdata/run$1:/input;$CFS/m4386/chester/flows_testing:/output;/global/cscratch1/sd/chester/tmpfiles:/tmp:perNodeCache=size=100G" --env-file=$HOME/shifter.env --module=none $HOME/globus_flows/run_compute_fit_mpi.sh $1 $2
