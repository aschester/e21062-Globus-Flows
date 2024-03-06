#!/usr/bin/env python3

##
# @file:  deploy_flow.py
# @brief: Deploy a new flow or update an existing one.
# See https://github.com/globus/globus-flows-trigger-examples.
#

import argparse
import json

from flows_service import create_flows_client


def deploy_flow():
    """Deploy or update a flow.

    Returns
    -------
    str, str
        Flow UUID and scope.

    """
    args = parse_args()
    fc = create_flows_client()

    # Get flow and input schema definitions
    with open(args.flowdef, "r") as f:
        flow_def = f.read()

    with open(args.schema, "r") as f:
        schema = f.read()

    if args.flowid:
        # Assume we're updating an existing flow
        flow_id = args.flowid
        flow = fc.update_flow(
            flow_id=flow_id,
            title=args.title,
            definition=json.loads(flow_def),
            input_schema=json.loads(schema),
        )
        print(f"Updated flow {flow_id}")

    else:
        # Deploy a new flow
        flow = fc.create_flow(
            title=args.title,
            definition=json.loads(flow_def),
            input_schema=json.loads(schema),
        )
        flow_id = flow["id"]
        print(f"Deployed flow {flow_id}")

    return flow_id, flow["globus_auth_scope"]


def parse_args():
    """Parse arguments and return an argparse.Namespace.

    """
    parser = argparse.ArgumentParser(
        description="Deploy a flow for use with trigger examples."
    )
    parser.add_argument(
        "--flowdef",
        required=True,
        help="Name of file containing the flow definition.",
    )
    parser.add_argument(
        "--schema",
        required=True,
        help="Name of file containing the input schema definition.",
    )
    parser.add_argument(
        "--title",
        default="My Example Flow",
        help="Flow title. [default: 'My Example Flow']",
    )
    parser.add_argument(
        "--flowid", help="Flow ID; used only when updating a flow definition"
    )
    parser.set_defaults(verbose=True)

    return parser.parse_args()


if __name__ == "__main__":
    """The main: Deploy or update the flow.

    """
    flow_id, scope = deploy_flow()
    print(f"Deployed flow with ID : {flow_id}\nScope : {scope}")
