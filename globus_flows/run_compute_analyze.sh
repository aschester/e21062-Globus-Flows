#!/bin/bash

# Format input:

run=$1
fmtrun=$(printf "%04d" $1)
nsegs=$2

# Set paths, copy input to the node for performant I/O:

tmpin=/tmp/tmprun$run-$SLURM_JOB_ID-$SLURMD_NODENAME
tmpout=/tmp
#tmpout=$PSCRATCH

logfile=$HOME/globus_flows/flow_logs/analysis-$SLURM_JOB_ID-$SLURMD_NODENAME-run$run.out
cat <<EOF >> $logfile
JobID   $SLURM_JOB_ID
Time    $SLURM_JOB_START_TIME
Node    $SLURMD_NODENAME
Tasks   $SLURM_CPUS_PER_TASK
DirIn   $input
DirOut  $output
NSegs   $nsegs
Image   $SHIFTER_IMAGEREQUEST

EOF

cp -rv /input $tmpin >> $logfile 2>&1

# Build all segments into the TChain for analysis. The trailing slashes
# on the dirs are necessary... sigh:
/global/cfs/cdirs/m4386/e21062_flows/software/betasort/betasort \
    $tmpin/ $tmpout/ $run $nsegs >> $logfile 2>&1

rm -rf $tmpin
mv $tmpout/run-$fmtrun-sorted.root /output
