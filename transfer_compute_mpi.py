#!/usr/bin/env python3

##
# @file:  transfer_compute_mpi.py
# @brief: Run a flow to transfer data to NERSC and perform compute tasks on
#         Perlmutter before transferring analyzed results to FRIB. The flow
#         can be triggered using python watchdog or run manually by specifying
#         an input directory.
#

import os
import sys
import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
import time

import globus_sdk
from globus_compute_sdk import Client
from flows_service import create_flows_client
from dirwatch import DirectoryTrigger


def run_flow(event_file=None):
    """Configure and run the flow.

    Parameters
    ----------
    event_file : str
        Full path of the event file which triggers the flow. For untriggered 
        flows, the event_file is None [default=None]. 

    Throws
    ------
    RuntimeError
        If any compute endpoints are not online.

    """
    args = parse_args()

    #############################
    # Endpoints for collections #
    #############################
    
    frib_dtn_id  = "9656eff2-8105-445c-8501-154dfe1d88e5"
    nersc_dtn_id = "9d6d994a-6d04-11e5-ba46-22000b92c6ec"

    ############################################
    # Setup paths for transfer and compute I/O #
    ############################################

    # Get the run directory from the trigger file path or argument:
    
    if args.watchdir:
        base_dir       = event_file
        pipeline_input = base_dir.replace("/cephfs", "")
    else:
        base_dir       = args.rundir.rstrip("/")
        pipeline_input = args.rundir.replace("/cephfs", "")
        
    run_dir = os.path.basename(base_dir)
    run_num = int(run_dir[3:])
        
    # Top level paths (on Globus):

    transfer_toplevel     = "/global/cfs/cdirs/m4386/e21062_flows/rawdata"
    fit_toplevel          = "/global/cfs/cdirs/m4386/e21062_flows/fitted"
    converted_toplevel    = "/global/cfs/cdirs/m4386/e21062_flows/converted"
    analyzed_toplevel     = "/global/cfs/cdirs/m4386/e21062_flows/analyzed"
    analyzed_output_fname = f"run-{run_num}-sorted.root"

    # Configure paths for pipeline steps:

    transfer_path  = os.path.join(transfer_toplevel, run_dir)
    fit_path       = os.path.join(fit_toplevel, run_dir)
    converted_path = os.path.join(converted_toplevel, run_dir)
    analyzed_path  = os.path.join(analyzed_toplevel, analyzed_output_fname)
    log_path       = "/global/homes/c/chester/globus_flows/flow_logs"

    # Final pipeline output. This must be a Globus path:
    
    pipeline_output_toplevel = "/mnt/sci-dtn/e21062_2/nersc_analysis"
    pipeline_output = os.path.join(
        pipeline_output_toplevel, analyzed_output_fname
    )
    
    logging.root.info(f"Sending:   {pipeline_input} --> {transfer_path}")
    logging.root.info(f"Fit:       {fit_path}")
    logging.root.info(f"Converted: {converted_path}")
    logging.root.info(f"Analyzed:  {analyzed_path}")
    logging.root.info(f"Receiving: {analyzed_path} --> {pipeline_output}")

    #########################################
    # Setup compute endpoints and functions #
    #########################################

    # Compute endpoints at NERSC for FRIB analysis:
    
    compute_fit_ep_id      = "ff16dcd1-0632-4fdd-8b0c-d239d4f1b889"
    compute_convert_ep_id  = "f4d90d3e-ed80-4aae-b0de-62fdbe2a0739"
    compute_analysis_ep_id = "5080ade8-846b-4964-88a1-2c602d5d38f4"

    # Function UUIDs for remote execution on the above endpoints:
    
    fit_function_id      = "42e3e64f-4d1e-4681-9a3e-cc9533d7933e"    
    convert_function_id  = "2be66611-af61-4a9e-a0b2-3407675771c7"
    analysis_function_id = "62f120cd-9249-4124-b9df-44f8e1c44fe1"
    
    # Check the endpoint status:
    
    if not endpoint_online(compute_fit_ep_id):
        raise RuntimeError(
            f"Trace-fitting compute endpoint {compute_fit_ep_id} "
            "is not online!"
        )
    if not endpoint_online(compute_convert_ep_id):
        raise RuntimeError(
            f"ROOT conversion compute endpoint {compute_convert_ep_id} "
            "is not online!"
        )
    if not endpoint_online(compute_analysis_ep_id):
        raise RuntimeError(
            f"Analysis compute endpoint {compute_analysis_ep_id} "
            "is not online!"
        )

    ##################
    # Configure flow #
    ##################
        
    flow_id = "babd88e5-d31d-48c7-b3a0-b765389b5c22"
    fc = create_flows_client(
        flow_id=flow_id, collection_ids=[frib_dtn_id, nersc_dtn_id]
    )
    flow_label = f"FRIB-NERSC Analysis Pipeline Run {run_num}"

    # Flow input schema:

    flow_input = {
        "top_rawdata_dir": {
            "endpoint_id": nersc_dtn_id,
            "path": transfer_toplevel
        },
        "top_fit_dir": {
            "endpoint_id": nersc_dtn_id,
            "path": fit_toplevel
        },
        "top_converted_dir": {
            "endpoint_id": nersc_dtn_id,
            "path": converted_toplevel
        },
        "top_analyzed_dir": {
            "endpoint_id": nersc_dtn_id,
            "path": analyzed_toplevel
        },
        "compute_log_dir": {
            "endpoint_id": nersc_dtn_id,
            "path": log_path
        },
        "rawdata": {
            "source": {
                "id": frib_dtn_id,
                "path": pipeline_input,
            },
            "destination": {
                "id": nersc_dtn_id,
                "path": transfer_path,
            },
            "filter_rules": [
                {
		    "DATA_TYPE": "filter_rule",
		    "method": "include",
		    "type": "file",
		    "name": "*.evt"
                },
                {
		    "DATA_TYPE": "filter_rule",
		    "method": "exclude",
		    "type": "file",
		    "name": "*"
                }
	    ],
            "sync_level": 3,
            "notify_on_succeeded": False,
            "notify_on_failed": True,
            "notify_on_inactive": True,
            "recursive_tx": True
        },
        "fit_dir": {
            "endpoint_id": nersc_dtn_id,
            "path": fit_path
        },
        "fit": {
            "endpoint": compute_fit_ep_id,
            "function": fit_function_id,
            "kwargs": {
                "endpoint_id": compute_fit_ep_id,
                "input_path": transfer_path,
                "output_path": fit_path
            },
        },
        "converted_dir": {
            "endpoint_id": nersc_dtn_id,
            "path": converted_path
        },
        "convert": {
            "endpoint": compute_convert_ep_id,
            "function": convert_function_id,
            "kwargs": {
                "endpoint_id": compute_convert_ep_id,
                "input_path": fit_path,
                "output_path": converted_path
            },
        },
        "analyze": {
            "endpoint": compute_analysis_ep_id,
            "function": analysis_function_id,
            "kwargs": {
                "endpoint_id": compute_analysis_ep_id,
                "input_path": converted_path,
                "output_path": analyzed_toplevel
            },
        },
        "pipeline_output": {
            "source": {
                "id": nersc_dtn_id,
                "path": analyzed_path
            },
            "destination": {
                "id": frib_dtn_id,
                "path": pipeline_output
            },
            "sync_level": 3,
            "notify_on_succeeded": False,
            "notify_on_failed": True,
            "notify_on_inactive": True,
            "recursive_tx": False
        }
    }

    ################
    # Run the flow #
    ################

    # FRIB Flow Administrators group:
    admins = "urn:globus:groups:id:a936c054-d004-11ee-8305-01ad603c66f1"

    logging.info(f"Preparing to run flow {flow_label} as UUID {flow_id}")
    
    # SpecificFlowClient unfortunately lacks the dry_run parameter, so all
    # we do is return at this point, prior to validating the input at runtime:
   
    if args.dry_run:
        logging.info(f"Running flow {flow_label} as UUID {flow_id} --dry-run")
    else:
        logging.info(f"Running flow {flow_label} as UUID {flow_id}")
        flow_run_request = fc.run_flow(
            body=flow_input,
            label=flow_label,
            run_monitors=[admins],
            tags=["Transfer", "Compute", "FRIB"],
        )
    
def endpoint_online(endpoint_id):
    """Check the endpoint status and return True if it is online.

    Parameters
    ----------
    endpoint_id : str
        Endpoing UUID.
    
    Returns
    -------
    bool
        True if the endpoint is online, False otherwise.

    """
    gcc = Client()
    name = gcc.get_endpoint_metadata(endpoint_id)["name"]
    hostname = gcc.get_endpoint_metadata(endpoint_id)["hostname"]
    status = gcc.get_endpoint_status(endpoint_id)["status"]
    
    logging.root.info(f"Endpoint {name} on {hostname} status: '{status}'")

    if status != "online":
        return False
    
    return True


def parse_args():
    """Parse arguments and return an argparse.Namespace.

    Returns
    -------
    argparse.Namespace
        Parsed arguments from ArgumentParser.parse_args.

    """
    parser = argparse.ArgumentParser(
        description="Batch run a pre-registered function as part of a "
        "Globus flow. The flow may be triggered by the creation of a new " 
        "run directory in the watched directory or manually for an input "
        "directory."
    )
    
    input_group = parser.add_argument_group(
        "input configuration", "Input configuration for the flow."
    )
    input_group.add_argument(
        "--trigger-delay",
        type=int,
        nargs="?",
        default=30,
        help="Delay applied to the flow start in seconds to ensure all "
        "data is copied in [default=30]."
    ) 
    
    mutex_group = input_group.add_mutually_exclusive_group(required=True)
    mutex_group.add_argument(
        "--watchdir",
        type=str,
        nargs="?",
        help="Directory path to watch for filesystem event triggers. "
        "Mutually exclusive with --rundir."
    )
    mutex_group.add_argument(
        "--rundir",
        type=str,
        nargs="?",
        help="Path of input directory for the analysis pipeline. Mutually "
        "exclusive with --watchdir."
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Setup the flow without submitting to Globus."
    )

    parser.set_defaults(verbose=True)
    
    return parser.parse_args()


if __name__ == "__main__":
    """The main: Runs when the script is executed.

    """
    args = parse_args()

    # Configure the trigger for starting the pipeline and run it:
    
    try:
        if args.watchdir:
            trigger = DirectoryTrigger(
                watch_dir=os.path.expanduser(args.watchdir),
                delay=args.trigger_delay,
                FlowRunner=run_flow
            )        
            trigger.run()
        else:
            run_flow()
    except globus_sdk.FlowsAPIError as e:
        logging.root.error(f"API Error: {e.code} {e.message}")
        logging.root.error(f"API Error: {e.text}")
        sys.exit(1)
