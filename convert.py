#!/usr/bin/env python3

##
# @file:  convert.py
# @brief: Compute function to convert fitted data to ROOT format.
#

import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

from globus_compute_sdk import Client


# Registered as: 2c68f1c5-b878-4704-a294-0f9274076541


def convert(endpoint_id, ncpus, input_path, output_path):
    """Registered function for converting fitted dat to ROOT format.

    Parameters
    ----------
    endpoint_id : str
        Endpoint UUID where the function is run.
    ncpus : int
        Number of CPUs per task.
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
    int
        0 (Success).

    """
    import os
    import fnmatch
    from globus_compute_sdk import Executor
    import concurrent.futures
    
    def callback(ncpus, input_path, output_path, run, seg):
        """Callback function to run using the Executor.

        Parameters
        ----------
        ncpus : int
            Number of CPUs to allocate for the job.
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
        int
            0 if success.

        """
        import subprocess
        process = subprocess.run(
            f"srun -N 1 -c {ncpus} shifter "
            "--image=fribdaq/frib-buster:v4.2 "
            f"--volume=/global/cfs/cdirs/m4386/opt-buster:/usr/opt;{input_path}:/input;{output_path}:/output;/global/cscratch1/sd/chester/tmpfiles:/tmp:perNodeCache=size=100G "
            "--module=none "
            "--env-file=/global/homes/c/chester/shifter.env "
            "/global/homes/c/chester/globus_flows/run_compute_convert.sh "
            f"{run} {seg}".split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return process.returncode

    # Configure the job:

    run = os.path.basename(input_path).replace("run", "")
    segments = len(fnmatch.filter(os.listdir(input_path), "*.evt"))

    if segments == 0:
        raise RuntimeError(f"No event files in {input_path}!")
    
    futures, results = [], []
    with Executor(endpoint_id=endpoint_id) as gce:
        for s in range(segments):
            futures.append(
                gce.submit(callback, ncpus, input_path, output_path, run, s)
            )
        # Must handle results inside the `with` statement before implicit
        # invocation of `.shutdown()`.
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    if not results:
        raise RuntimeError("Futures results list is empty!")    
            
    return results

def register_function():
    """Register the fitting function and return its UUID.

    """
    gcc = Client()
    uuid = gcc.register_function(
        convert, function_name="convert",
        description="""Convert event files with trace fit data to 
        ROOT format"""
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
        "-r", "--register",
        action="store_true",
        help="(Optional) Re-register the compute function."
    )

    return parser.parse_args()


if __name__ == "__main__":
    """main: Optionally re-register the function.

    """
    args = parse_args()
    if (args.register):
        uuid = register_function()
        print(f"Convert to ROOT function UUID: {uuid}")
