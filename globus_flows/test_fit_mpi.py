#!/usr/bin/env python3

##
# @file test_fit_mpi.py
# @brief A callable test Compute function to fit traces in an FRIBDAQ event
# file using containerized MPI parallelism. Run from inside the virtual
# environment where the Globus Compute Python SDK is installed.
# @note This is intended for debugging/testing only! It is not a registered
# compute function which can be called from a flow.
#
# For help/usage: python ./test_fit_mpi.py --help
#

import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
import os
import fnmatch
import time

from globus_compute_sdk import Client


def parse_args():
    """Parse arguments and return an argparse.Namespace.

    Returns
    -------
    argparse.Namespace
        Parsed arguments from ArgumentParser.parse_args.

    """
    parser = argparse.ArgumentParser(
        description="Fit traces on a compute endpoint using MPI"
    )

    parser.add_argument(
        "--endpoint_id",
        type=str,
        nargs="?",
        default="ff16dcd1-0632-4fdd-8b0c-d239d4f1b889",
        help="Input endpoint UUID [default=frib-fit-mpi UUID]"
    )    
    parser.add_argument(
        "--input-path",
        type=str, nargs="?",
        default="/global/cfs/cdirs/m4386/e21062_flows/rawdata",
        help="Globus path for the input directory "
        "[default=/global/cfs/cdirs/m4386/e21062_flows/rawdata]"
    )    
    parser.add_argument(
        "--output-path",
        type=str,
        nargs="?",
        default="/global/cfs/cdirs/m4386/chester/flows_testing",
        help="Globus path for the output directory "
        "[default=/global/cfs/cdirs/m4386/chester/flows_testing]"
    )
    parser.add_argument(
        "--run",
        type=int,
        nargs="?",
        default=1217,
        help="Run number to fit [default=1217]"
    )
    parser.add_argument(
        "--segments",
        type=int,
        nargs="+",
        default=[0],
        help="Segment number(s) to fit [default=0]"
    )
    parser.set_defaults(verbose=True)
    
    return parser.parse_args()


def callback(input_path, output_path, run, seg):
    """Callback function to run using the Executor.
    
    Parameters
    ----------
    input_path : str
        Path to input raw data files, mounted at /input in the image.
    output_path : str
        Path to output fitted files, mounted at /output in the image.
    run, seg : int, int
        Run and segment number to analyze.

    Returns
    -------
    tuple : int, str, str
        (0, "", "") if success.

    """
    import subprocess
    p = subprocess.run(
        f"shifter --image=fribdaq/frib-buster:v4.2 --volume=/global/cfs/cdirs/m4386/opt-buster:/usr/opt;{input_path}:/input;{output_path}:/output;/global/cscratch1/sd/chester/tmpfiles:/tmp:perNodeCache=size=100G --module=none --env-file=/global/homes/c/chester/shifter.env /global/homes/c/chester/globus_flows/run_compute_fit_mpi.sh {run} {seg}".split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return (
        p.returncode, p.stdout.decode("UTF-8"), p.stderr.decode("UTF-8")
    ) 


###############################
# Remote execute the callback #
###############################

args = parse_args()
input_path = os.path.join(args.input_path, f"run{args.run:04}")

gcc = Client()
function_id = gcc.register_function(callback, function_name="callback")
batch = gcc.create_batch()
for s in args.segments:
    batch.add(
        function_id=function_id,
        args=(input_path, args.output_path, args.run, s)
    )
    
batch_res = gcc.batch_run(endpoint_id=args.endpoint_id, batch=batch)
r = gcc.get_batch_result(batch_res["tasks"][str(function_id)])

print(f"INIT: {r}")

def check_status(res):
    for k, v in res.items():
        if not "completion_t" in v:
            return False
    return True

while not check_status(r):
    time.sleep(5)
    r = gcc.get_batch_result(batch_res["tasks"][str(function_id)])

print(f"DONE: {r}")
