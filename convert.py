#!/usr/bin/env python3

##
# @file:  convert.py
# @brief: Compute function to convert fitted data to ROOT format.
#

import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

from globus_compute_sdk import Client


# Registered as: 2be66611-af61-4a9e-a0b2-3407675771c7


def callback(input_path, output_path, run, seg):
    """Callback function to run using the Executor.

    Parameters
    ----------
    input_path : str
        Path to input fitted files, mounted at /input in the image.
    output_path : str
        Path to output converted files, mounted at /output in the image.
    run : int
        Run number to analyze.
    seg : int
        Number of segments in the run.

    Throws
    ------
    CalledProcessError
        If subprocess.run return code != 0.

    Returns
    -------
    tuple : int, str, str
        (returncode, stdout, stderr). (0, "", "") if success.
    
    """
    import subprocess
    p = subprocess.run(
        f"shifter --image=fribdaq/frib-buster:v4.2 --volume=/global/cfs/cdirs/m4386/opt-buster:/usr/opt;{input_path}:/input;{output_path}:/output;/global/cscratch1/sd/chester/tmpfiles:/tmp:perNodeCache=size=1000G --module=none --env-file=/global/homes/c/chester/shifter.env /global/homes/c/chester/globus_flows/run_compute_convert.sh {run} {seg}".split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return (
        p.returncode, p.stdout.decode("UTF-8"), p.stderr.decode("UTF-8")
    )  


def convert(endpoint_id, input_path, output_path):
    """Registered function for converting fitted dat to ROOT format.

    Parameters
    ----------
    endpoint_id : str
        Endpoint UUID where the function is run.
    input_path : str
        Input data path contining the files to convert.
    output_path : str
        Output path for fitted data.

    Throws
    ------
    RuntimeError
        No datafiles found in the input path.

    Returns
    -------
    tuple : int, str, str
        (returncode, stdout, stderr). (0, "", "") if success.

    """
    import os
    import fnmatch
    import time
    from globus_compute_sdk import Client

    # Configure the job:

    run = os.path.basename(input_path).replace("run", "")
    segments = len(fnmatch.filter(os.listdir(input_path), "*.evt"))

    if segments == 0:
        raise RuntimeError(f"No event files in {input_path}!")

    gcc = Client()
    function_id = "8ca70c9d-887e-421e-939e-8caa223f44d7" # callback
    batch = gcc.create_batch()
    for s in range(segments):
        batch.add(
            function_id=function_id, args=(input_path, output_path, run, s)
        )

    batch_res = gcc.batch_run(endpoint_id=endpoint_id, batch=batch)
    results = gcc.get_batch_result(batch_res["tasks"][function_id])
        
    def check_status(res):
        for k, v in res.items():
            if not "completion_t" in v:
                return False
        return True
            
    while not check_status(results):
        time.sleep(30)
        results = gcc.get_batch_result(batch_res["tasks"][function_id])

    if not results:
        raise RuntimeError("Batch results dictionary is empty!")
        
    for k, v in results.items():
        if v["result"][0] != 0:
            raise RuntimeError(f"ERROR: {v['result']}")    
                                           
    return results


def register_batch():
    """Register the fitting function and return its UUID.

    """
    gcc = Client()
    uuid = gcc.register_function(
        convert, function_name="convert",
        description="Convert event files with trace fit data to "
        "ROOT format"
    )
    
    return uuid


def register_callback():
    """Register the callback function and return its UUID.

    """
    gcc = Client()
    uuid = gcc.register_function(
        callback, function_name="callback_convert",
        description="Callback function to convert event files with trace "
        "fit data to ROOT format"
    )
    
    return uuid


def parse_args():
    """Parse arguments and return an argparse.Namespace.

    """
    parser = argparse.ArgumentParser(
        description="""Convert event files with trace fit data to 
        ROOT format"""
    )
    parser.add_argument(
        "--register-batch",
        action="store_true",
        help="(Optional) Re-register the batch compute function."
    )
    parser.add_argument(
        "--register-callback",
        action="store_true",
        help="(Optional) Re-register the callback function."
    )

    return parser.parse_args()


if __name__ == "__main__":
    """main: Optionally re-register the function.

    """
    args = parse_args()
    if args.register_batch:
        uuid = register_batch()
        print(f"Convert to ROOT function UUID: {uuid}")
    if args.register_callback:
        uuid = register_callback()
        print(f"Callback function UUID: {uuid}")
