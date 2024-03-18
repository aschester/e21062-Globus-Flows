#!/bin/bash

##
# @file run_compute_fit_mpi.sh
# @brief Run the EventEditor to fit traces in an .evt file using MPI
# parallelism from in a containerized environment. Stage I/O in /tmp space,
# move staged output to CFS on completion. Log the output.
# @param 1 Run number.
# @param 2 Run segment.
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
cp -v $input $tmpin >> $logfile 2>&1
echo "... Done" >> $logfile

# Run the fitter and write to our log. mpirun's --use-hwthread-cpus and
# --oversubscribe options are some chicanery which allows us to run multiple
# Parsl-managed fitting tasks on a single node each using the number of 'CPUs'
# specified by the SBATCH --cpus-per-task option. A little unexpected compared
# to specifiying --ntasks-per-node but the resource usage looks OK, so:

echo "Fitting traces with mpirun -np $tasks $DAQBIN/EventEditor..." >> $logfile
mpirun --use-hwthread-cpus --oversubscribe -np $tasks \
     $DAQBIN/EventEditor \
     -s file://$tmpin \
     -S file://$tmpout \
     -l /usr/opt/ddastoys/lib/libFitEditorAnalytic.so \
     -n $nworkers \
     -c 2000 \
     -p mpi >> $logfile 2>&1

echo "Moving output and cleaning up..." >> $logfile
rm -vf $tmpin >> $logfile 2>&1 
mv -vf $tmpout $output >> $logfile  2>&1
echo "... All done" >> $logfile
