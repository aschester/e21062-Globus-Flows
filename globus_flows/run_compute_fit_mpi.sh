#!/bin/bash

##
# Run the EventEditor to fit traces in an .evt file. Stage I/O in /tmp space,
# move tmp output to CFS on completion. Log the output.
#

# Configure the runtime environment in the container:
 
source /usr/opt/daq/12.0-013/daqsetup.bash
export PATH=$MPI_ROOT/bin:$PATH
export LD_LIBRARY_PATH=$MPI_ROOT/lib:$LD_LIBRARY_PATH

# Format input:

run=$1
fmtrun=$(printf "%04d" $1)
seg=$(printf "%02d" $2)

# Set paths, copy input to the node for performant I/O:

input=/input/run-$fmtrun-$seg.evt
output=/output/$(echo $input | cut -d '/' -f 3 | cut -d '.' -f 1)-fitted.evt
tmpin=/tmp/tmpin-$SLURM_JOB_ID-run-$run-$seg.evt
tmpout=/tmp/tmpout-$SLURM_JOB_ID-run-$run-$seg.evt
#tmpin=$PSCRATCH/tmpin-$SLURM_JOB_ID-run-$run-$seg.evt
#tmpout=$PSCRATCH/tmpout-$SLURM_JOB_ID-run-$run-$seg.evt

tasks=$SLURM_CPUS_PER_TASK
nworkers=`expr $tasks - 3` # 3 reserved for fan-in, fan-out, sort (MPI only!)

# Using SLURM stdout and stderr redirection does not work for compute, as the
# Globus manager is doing quite a lot of overhead work. Therefore, we define
# our own log file and write to that one:

logfile=$HOME/globus_flows/flow_logs/fitoutput-run$run-$seg-$SLURM_JOB_ID-$SLURMD_NODENAME.out
cat <<EOF >> $logfile
JobID   $SLURM_JOB_ID
Time    $SLURM_JOB_START_TIME
Node    $SLURMD_NODENAME
Tasks   $tasks
Workers $nworkers
FileIn  $input
FileOut $output
DAQBIN  $DAQBIN
MPI     $(which mpirun)
Image   $SHIFTER_IMAGEREQUEST

EOF

echo "Copying input..." >> $logfile
cp -v $input $tmpin 2>&1 >> $logfile
echo "... Done" >> $logfile

# Run the fitter and write to our log:

mpirun --use-hwthread-cpus --oversubscribe -np $tasks $DAQBIN/EventEditor \
     -s file://$tmpin \
     -S file://$tmpout \
     -l /usr/opt/ddastoys/lib/libFitEditorAnalytic.so \
     -n $nworkers \
     -c 2000 \
     -p mpi 2>&1 >> $logfile

echo "Moving output and cleaning up..." >> $logfile
rm -vf $tmpin 2>&1 >> $logfile
mv -vf $tmpout $output 2>&1 >> $logfile
echo "... All done" >> $logfile
