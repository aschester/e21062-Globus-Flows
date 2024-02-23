#!/usr/bin/env python3

##
# @file:  analyze.py
# @brief: Compute function to analyze fitted data to ROOT format.
#

import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

from globus_compute_sdk import Client


# Registered as: f097b86b-6305-4946-beac-9e03abe5955d


def analyze(ncpus=1, run=None):
    """Registered function to analyze data with the Liddick group betasort.

    Parameters
    ----------
    ncpus : int
        Number of CPUs per task.
    run : int
        The run number without leading zeroes.

    Raises
    ------
    RuntimeError
        If a run number is not passed as an argument.
    CalledProcessError
        If subprocess.run return code != 0.

    Returns
    -------
    int
        0 (Success).

    """
    import subprocess
    if run is None:
        raise RuntimeError('Expected run number as argument but got None!')
    process = subprocess.run(
        f'srun -N 1 -c {ncpus} shifter '
        f'--env-file=/global/homes/c/chester/shifter.env '
        f'/global/homes/c/chester/globus_flows/run_compute_analyze.sh '
        f'{run}'.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    process.check_returncode() # throws if non-zero
    
    return process.returncode  # return 0 (success)


def register_function():
    """Register the fitting function and return its UUID.

    """
    gcc = Client()
    uuid = gcc.register_function(
        analyze, function_name='analyze',
        description='Analyze data with betasort'
    )
    
    return uuid    
    

def parse_args():
    """Parse arguments and return an argparse.Namespace.

    """
    parser = argparse.ArgumentParser(
        description='Betasort analysis'
    )
    parser.add_argument(
        '-r', '--register',
        action='store_true',
        help='(Optional) Re-register the compute function.'
    )

    return parser.parse_args()


if __name__ == '__main__':
    """main: Optionally re-register the function.

    """
    args = parse_args()
    if (args.register):
        uuid = register_function()
        print(f'Betasort analysis function UUID: {uuid}')
