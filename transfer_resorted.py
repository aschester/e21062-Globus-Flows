#!/usr/bin/env python3

##
# @file: transfer_resorted.py
# @brief: Run a flow to transfer data from NERSC to the FRIB DTN.
#

import os
import sys
import argparse
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
import time

import globus_sdk
from globus_compute_sdk import Client
from flows_service import create_flows_client


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

    logging.root.info(
        f"Transferring: {args.source_path} --> {args.destination_path}"
    )

    ##################
    # Configure flow #
    ##################
    
    flow_id = "47557a0b-75ba-4df1-8a85-f5fb556c31a4"
    fc = create_flows_client(
        flow_id=flow_id, collection_ids=[args.source_id, args.destination_id]
    )
    flow_label = "Transfer Data From NERSC To FRIB"

    # Flow input schema:

    flow_input = {
        "transfer": {
            "source": {
                "id": args.source_id,
                "path": args.source_path
            },
            "destination": {
                "id": args.destination_id,
                "path": args.destination_path
            },
            "filter_rules": [
                {
		    "DATA_TYPE": "filter_rule",
		    "method": "include",
		    "type": "file",
		    "name": "*.root"
                },
                {
		    "DATA_TYPE": "filter_rule",
		    "method": "exclude",
		    "type": "file",
		    "name": "*"
                },
                {
		    "DATA_TYPE": "filter_rule",
		    "method": "exclude",
		    "type": "dir",
		    "name": "*"
                }
	    ],
            "sync_level": 3,
            "notify_on_succeeded": False,
            "notify_on_failed": True,
            "notify_on_inactive": True,
            "recursive_tx": True
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
            tags=["Transfer", "FRIB"],
        )


def parse_args():
    """Parse arguments and return an argparse.Namespace.

    Returns
    -------
    argparse.Namespace
        Parsed arguments from ArgumentParser.parse_args.

    """
    parser = argparse.ArgumentParser(
        description="Transfer resorted data from NERSC to FRIB"
    )

    parser.add_argument(
        "--source-id",
        type=str,
        nargs="?",
        default="9d6d994a-6d04-11e5-ba46-22000b92c6ec",
        help="Source endpoint ID [default=NERSC]"
    )
    
    parser.add_argument(
        "--source-path",
        type=str, nargs="?",
        default="/global/cfs/cdirs/m4386/e21062_flows/sorted-RSL",
        help="Globus path for the source directory "
        "[default=/global/cfs/cdirs/m4386/e21062_flows/sorted-RSL]"
    )    
    parser.add_argument(
        "--destination-id",
        type=str,
        nargs="?",
        default="9656eff2-8105-445c-8501-154dfe1d88e5",
        help="Destination endpoint ID [default=FRIB]"
    )
    parser.add_argument(
        "--destination-path",
        type=str,
        nargs="?",
        default="/mnt/sci-dtn/e21062_2/nersc_analysis",
        help="Globus path for the destination directory "
        "[default=/mnt/sci-dtn/e21062_2/nersc_analysis]"
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
    try:
        run_flow()
    except globus_sdk.FlowsAPIError as e:
        logging.root.error(f"API Error: {e.code} {e.message}")
        logging.root.error(f"API Error: {e.text}")
        sys.exit(1)
        
