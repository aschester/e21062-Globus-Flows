#!/usr/bin/env python3

##
# @file:  convert.py
# @brief: Compute function to convert fitted data to ROOT format.
#

import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

from globus_compute_sdk import Client


# Registered as: d97891af-8c33-4d8e-8132-7436d79eff28


def convert(*args):
    """Registered function to convert event files with fit data to ROOT.

    Parameters
    ----------
    *args : tuple
        Tuple of ncpus, run, segment job parameters.

    Throws
    ------
    RuntimeError
        Incorrect number of arguments passed to the function.
    CalledProcessError
        If subprocess.run return code != 0.

    Returns
    -------
    int
        0 (Success).

    """
    import subprocess
    if len(args) != 3:
        raise RuntimeError(f'Expected 3 args but got {args}!')
    process = subprocess.run(
        f'srun -N 1 -c {args[0]} shifter '
        f'--env-file=/global/homes/c/chester/shifter.env '
        f'/global/homes/c/chester/globus_flows/run_compute_convert.sh '
        f'{args[1]} {args[2]}'.split(),
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
        convert, function_name='convert',
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
        print(f'Convert to ROOT function UUID: {uuid}')
