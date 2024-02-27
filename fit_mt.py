#!/usr/bin/env python3

##
# @file:  fit_mt.py
# @brief: Compute function to fit traces in an FRIBDAQ event file.
#

import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

from globus_compute_sdk import Client


# Registered as: c33bd4db-71cc-4852-96e1-7497f38658a4


def fit_mt(endpoint_id, ncpus, input_path, output_path):
    """Registered function to fit trace data.

    Parameters
    ----------
    endpoint_id : str
        Endpoint UUID where the function is run.
    ncpus : int
        Number of CPUs per task.
    input_path : str
        Input data path contining the files to fit.
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
            Path to input raw data files, mounted at /input in the image.
        output_path : str
            Path to output fitted files, mounted at /output in the image.
        run, seg : int, int
            Run and segment number to analyze.

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
            "/global/homes/c/chester/globus_flows/run_compute_fit_mt.sh "
            f"{run} {seg}".split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        process.check_returncode() # throws if non-zero
        
        return process.returncode  # return 0 (success)
    
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
        fit_mt, function_name="fit_mt",
        description="Fit traces in an analysis pipeline with the "
        "FRIBDAQ EventEditor using threaded parallelism"
    )
    
    return uuid    
    

def parse_args():
    """Parse arguments and return an argparse.Namespace.

    """
    parser = argparse.ArgumentParser(
        description="Fit traces for a single run segment in the shifter "
        "container at NERSC"
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
        print(f"Fit function UUID: {uuid}")
