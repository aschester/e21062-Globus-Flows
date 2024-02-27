import sys
import logging
import subprocess

from globus_compute_sdk import Client

logging.basicConfig(
    format='%(asctime)s %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    stream=sys.stdout,
    level=logging.INFO
)

client = Client()
endpoints = client.get_endpoints() # They're all at NERSC so this is fine

for ep in endpoints:
    uuid = ep["uuid"]
    name = client.get_endpoint_metadata(uuid)["name"]

    logging.info(f"Deleting endpoint {name} with UUID {uuid}")

    client.delete_endpoint(uuid)
