#!/bin/bash

##
# @file run_compute_analyze.sh
# @brief Run the Liddick group betasort code from in a containerized
# environment. Stage I/O in /tmp space, move staged output to CFS on
# completion. Log the output.
# @param 1 Run number.
# @param 2 Number of segments. If 0 (zero), sort only the first segment.
#

# Format input:

run=$1
fmtrun=$(printf "%04d" $1)
nsegs=$2

# Set paths, copy input to the node for performant I/O:

tmpin=/tmp/tmprun$run-$SLURM_JOB_ID-$SLURMD_NODENAME
tmpout=/tmp
#tmpin=$PSCRATCH/tmprun$run-$SLURM_JOB_ID-$SLURMD_NODENAME
#tmpout=$PSCRATCH

logfile=$HOME/globus_flows/flow_logs/analysis-run$run-$SLURM_JOB_ID-$SLURMD_NODENAME.out
cat <<EOF >> $logfile
JobID   $SLURM_JOB_ID
Time    $SLURM_JOB_START_TIME
Node    $SLURMD_NODENAME
DirIn  	/input/*.root
DirOut  /output/run-$fmtrun-sorted.root
NSegs   $nsegs
Image   $SHIFTER_IMAGEREQUEST

EOF

echo "Copying input..." >> $logfile
cp -rv /input $tmpin >> $logfile 2>&1
echo "... Done\n" >> $logfile

# Build all segments into the TChain for analysis. The trailing slashes
# on the dirs are necessary... sigh...:
/global/cfs/cdirs/m4386/e21062_flows/software/betasort/betasort \
    $tmpin/ $tmpout/ $run $nsegs >> $logfile 2>&1

echo "Moving output and cleaing up..." >> $logfile
rm -vrf $tmpin/ >> $logfile 2>&1
mv -vf $tmpout/run-$fmtrun-sorted.root /output >> $logfile 2>&1
echo "... All done" >> $logfile
