#!/bin/bash

shifter --image=fribdaq/frib-buster:v4.2 --volume="/global/cfs/cdirs/m4386/opt-buster:/usr/opt;/global/cfs/cdirs/m4386/chester/fitted:/fitted;/global/cfs/cdirs/m4386/chester/converted:/converted;/global/cscratch1/sd/chester/tmpfiles:/tmp:perNodeCache=size=100G" --env-file=/global/homes/c/chester/shifter.env --module=none /global/homes/c/chester/run_compute_convert.sh $1 $2
