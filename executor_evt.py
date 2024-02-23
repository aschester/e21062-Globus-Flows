#!/usr/bin/env python3

##
# @file:  executor_evt.py
# @brief: Generic compute function for launching Executor array jobs which
#         processFRIBDAQ event files (extension .evt).
#

import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

from globus_compute_sdk import Client


# Registered as: e7e6549c-d3d8-47c2-86c8-261b5c4df474


def executor_evt(endpoint_id, function_id, ncpus, input_path):
    """Run mulitple instances of a function which takes FRIBDAQ event files 
    as input. The expected input directory format is /path/to/runXXXX 
    containing the event files. The run number is extracted from this path.
    
    Parameters
    ----------
    endpoint_id : str
        Endpoint UUID to where this function is run.
    function_id : str
        Registered function UUID run by the Executor.
    input_path : str
        Remote endpoint location for input data.
    ncpus : int
        Number of CPUs allocated to the task. Sets the value of 
        --cpus-per-task when invoking srun on the compute endpoint.

    Throws
    ------
    RuntimeError
        No input files in the provided path.
    RuntimeError
        If the futures results list is empty.

    Returns
    -------
    list : Futures
        List of Futures containing the results.

    """
    import os
    import fnmatch
    from globus_compute_sdk import Executor
    import concurrent.futures

    # Configure the job:

    run = os.path.basename(input_path).replace('run', '')
    segments = len(fnmatch.filter(os.listdir(input_path), '*.evt'))

    if segments == 0:
        raise RuntimeError(f'No event files in {input_path}!')

    # Run a registered function using an Executor and gather results as
    # they arrive:
    
    futures, results = [], []
    with Executor(endpoint_id=endpoint_id) as gce:
        for s in range(segments):
            futures.append(
                gce.submit_to_registered_function(function_id, (ncpus, run, s))
            )
        # NOTA BENE: handling results "as they arrive" must happen before the
        # executor is shutdown.  Since this executor was used in a `with`
        # statement, then to stream results, we must *stay* within the `with`
        # statement.  Otherwise, at the unindent, `.shutdown()` will be
        # implicitly invoked (with default arguments) and the script will not
        # continue until *all* of the futures complete.
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    if not results:
        raise RuntimeError('Futures results list is empty!')
            
    return results

    
def register_function():
    """Register the fitting function and return its UUID.

    """
    gcc = Client()
    uuid = gcc.register_function(
        executor_evt, function_name='executor_evt',
        description='Run a multiple instances of registered function '
        'using the Executor at NERSC which operates on FRIBDAQ event '
        'files (*.evt)'
    )
    
    return uuid    
    

def parse_args():
    """Parse arguments and return an argparse.Namespace.

    """
    parser = argparse.ArgumentParser(
        description='Run a pre-registered function in a loop using '
        'the Executor.'
    )
    parser.add_argument(
        '-r', '--register',
        action='store_true',
        help='(Optional) Re-register the executor function.'
    )

    return parser.parse_args()


if __name__ == '__main__':
    """main: Optionally re-register the function.

    """
    args = parse_args()
    if (args.register):
        uuid = register_function()
        print(f'Executor function UUID: {uuid}')
