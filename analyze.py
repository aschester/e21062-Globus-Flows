#!/usr/bin/env python3

##
# @file:  analyze.py
# @brief: Compute function to analyze fitted data to ROOT format.
#

import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

from globus_compute_sdk import Client


# Registered as: 62f120cd-9249-4124-b9df-44f8e1c44fe1


def analyze(endpoint_id, input_path, output_path):
    """Registered function to analyze data with the Liddick group betasort.

    Parameters
    ----------
    endpoint_id : str
        Endpoint UUID where the function is run.
    input_path : str
        Input data path contining the files to analyze.
    output_path : str
        Output path for analyzed data.

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
    from globus_compute_sdk import Executor
    import concurrent.futures
    
    def callback(input_path, output_path, run, nsegs):
        """Callback function to run using the Executor.

        Parameters
        ----------
        input_path : str
            Path to input converted files, mounted at /input in the image.
        output_path : str
            Path to output analyzed files, mounted at /output in the image.
        run : int
            Run number to analyze.
        nsegs : int
            Number of segments to include in the analysis.

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
            f"shifter --image=fribdaq/frib-buster:v4.2 --volume=/global/cfs/cdirs/m4386/opt-buster:/usr/opt;{input_path}:/input;{output_path}:/output;/global/cscratch1/sd/chester/tmpfiles:/tmp:perNodeCache=size=1000G --module=none --env-file=/global/homes/c/chester/shifter.env /global/homes/c/chester/globus_flows/run_compute_analyze.sh {run} {nsegs}".split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return (
            p.returncode, p.stdout.decode("UTF-8"), p.stderr.decode("UTF-8")
        ) 

    # Configure the job:

    run = os.path.basename(input_path).replace("run", "")
    segments = len(fnmatch.filter(os.listdir(input_path), "*.root"))

    if segments == 0:
        raise RuntimeError(f"No event files in {input_path}!")
    
    # Run the function:
    
    with Executor(endpoint_id=endpoint_id) as gce:
        future = gce.submit(
            callback, input_path, output_path, run, segments
        )
        # Must handle results inside the `with` statement before implicit
        # invocation of `.shutdown()`.
        result = future.result()

    if result[0] != 0:
        raise RuntimeError(f"ERROR: {result}")
            
    return result


def register_function():
    """Register the fitting function and return its UUID.

    """
    gcc = Client()
    uuid = gcc.register_function(
        analyze, function_name="analyze",
        description="Analyze data with betasort"
    )
    
    return uuid    
    

def parse_args():
    """Parse arguments and return an argparse.Namespace.

    """
    parser = argparse.ArgumentParser(
        description="Betasort analysis"
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
        print(f"Betasort analysis function UUID: {uuid}")
