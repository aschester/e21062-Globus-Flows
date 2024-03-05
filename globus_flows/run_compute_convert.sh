#!/bin/bash

##
# @file run_compute_analyze.sh
# @brief Convert EventEditor output too ROOT format in a containerized
# environment. Stage I/O in /tmp space, move staged output to CFS on
# completion. Log the output.
# @param 1 Run number.
# @param 2 Number of segments. If 0 (zero), sort only the first segment.
#

# Configure the runtime environment in the container:

source /usr/opt/root/root-6.24.06/bin/thisroot.sh

# Format input:

run=$1
fmtrun=$(printf "%04d" $1)
seg=$(printf "%02d" $2)

# Set paths, copy input to the node for performant I/O:

input=/input/run-$fmtrun-$seg-fitted.evt
output=/output/$(echo $input | cut -d '/' -f 3 | cut -d '.' -f 1).root
tmpin=/tmp/tmpin-$SLURM_JOB_ID-run-$run-$seg.evt
tmpout=/tmp/tmpout-$SLURM_JOB_ID-run-$run-$seg.root
#tmpin=$PSCRATCH/tmpin-$SLURM_JOB_ID-run-$run-$seg.evt
#tmpout=$PSCRATCH/tmpout-$SLURM_JOB_ID-run-$run-$seg.root

# Using SLURM stdout and stderr redirection does not work for compute, as the
# Globus manager is doing quite a lot of overhead work. Therefore, we define
# our own log file and write to that one:

logfile=$HOME/globus_flows/flow_logs/converted-run$run-$seg-$SLURM_JOB_ID-$SLURMD_NODENAME.out
cat <<EOF >> $logfile
JobID   $SLURM_JOB_ID
Time    $SLURM_JOB_START_TIME
Node    $SLURMD_NODENAME
FileIn  $input
FileOut $output
ROOT    $(which root)
Image   $SHIFTER_IMAGEREQUEST

EOF

echo "Copying input..." >> $logfile
cp -v $input $tmpin >> $logfile 2>&1
echo "... Done" >> $logfile

/usr/opt/ddastoys/bin/eeconverter -s file://$tmpin -f $tmpout >> $logfile 2>&1

echo "Moving output and cleaning up..." >> $logfile
rm -vf $tmpin >> $logfile 2>&1
mv -vf $tmpout $output >> $logfile 2>&1
echo "... All done" >> $logfile
