import sys
import logging
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    stream=sys.stdout,
    level=logging.INFO
)
import subprocess
import time

from globus_compute_sdk import Client

while True:
    client = Client()
    endpoints = client.get_endpoints() # They're all at NERSC so this is fine
    
    for ep in endpoints:
        uuid = ep["uuid"]
        name = client.get_endpoint_metadata(uuid)["name"]
        hostname = client.get_endpoint_metadata(uuid)["hostname"]
        status = client.get_endpoint_status(uuid)["status"]
        
        logging.info(
            f"Endpoint {name} on {hostname} with UUID {uuid} status: '{status}'"
        )
        
        if status != "online":
            logging.info(f"Starting endpoint {name} {uuid}")
            subprocess.run(
                f"/global/homes/c/chester/globus_flows/globus_compute_venv/bin/globus-compute-endpoint start {name}".split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            status = client.get_endpoint_status(uuid)["status"]
            tries = 0
            while status != "online" and tries < 10:
                time.sleep(1)
                status = client.get_endpoint_status(uuid)["status"]
                tries = tries + 1
                
            if status == "online":
                logging.info(
                    f"Restarted endpoint {name} on {hostname} with UUID {uuid} status: '{status}'"
                )
            else:
                logging.error(f"ERROR: Failed to restart endpoint {name} on {hostname} with UUID {uuid}!")
    time.sleep(300)
                
