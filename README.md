# Automated Data Analysis Using Globus Flows
A. Chester  
Facility for Rare Isotope Beams  
640 S. Shaw Ln.  
East Lansing, MI 48924 USA  

5 March 2024  

## Introduction
This repository contains an automated workflow example for FRIB data analysis used during FDSi experiment e21062B (PI: H. Crawford) which ran 27 February to 4 March 2024. The workflow utilizes the computational resources available at NERSC to increase the throughput for compute-intensive tasks such as fitting ADC trace data. High-speed data transfer between FRIB and NERSC is done over ESnet, and the entire workflow--data transfer and analysis--is managed using a Globus Flow. Some familiarity with Globus, HPC computing (specifically at NERSC), and the e21062 analysis methods are assumed, though the overall framework is general enough to apply to other use cases. The e21062 flow software is written primarily in Python and makes heavy use of the Globus SDK and Globus Compute SDK.

## Globus Flows
A Globus Flow is composed of a series of _action providers_, which perform _actions_ as part of a _flow_. The service to run a file transfer between Globus collections is an example of an action provider. The associated action contains the results, status, and metadata associated with a particular invocation of the transfer action provider. A flow is a single operation which incorporates (possibly many) action providers in a defined order: for example, copying data from a source collection to a destination collection via some intermediary collection. Starting a flow with a particular set of inputs is called a _run_ or _flow run_. A number of action providers are hosted by Globus and can be used to construct custom flows.

### Flow Definitions
A flow _definition_, perhaps unsurprisingly, defines the relationship between the actions of a flow, implemented as a type of state machine. Flow definitions are JSON-formatted files written using a derivative of the Amazon States Language specific to Globus Flows. A simple transfer flow definition could consist of a single transfer action run by the transfer action provider.

### Flow Inputs
The input to a flow is known as an _input document_. Many (if not all) couture flows require custom inputs. A flow's _input schema_ can be used to validate a user's input document. If the input document does not conform to the expected format defined by the input schema, the flow run will not start. Input documents and schema are written using the JSON schema format. Returning to the transfer example, a transfer flow input schema could require source and destination paths as part of an input document. Any input documents which do not specify these paths would not be considered valid.

### Globus Compute
Globus Compute provides a "Function-as-a-Service" (FaaS) platform, allowing users to execute their code using a remote _compute endpoint_. The endpoint is run by the user and provides an interface which allows for remote function execution on some host system. Resource requirements and scaling are defined as part of the endpoint configuration. Remote execution of a function is performed by either calling the `.submit()` method of the Globus Compute `Executor` class or using the Globus Compute `Client` batching. Pre-registered functions can be invoked using both of these methods. Parsl is used by the Globus Compute platform to manage resources specified by the endpoint configuration. At NERSC, Parsl must interact with the Slurm scheduler to submit tasks to allocated resources.

## e21062 Example Flow
Before running the data analysis pipeline flow, the user must have:
1. An account at NERSC which is part of the e21062 analysis project m4386.
2. Familiarity with the [FRIBDAQ parallel trace fitting software](https://github.com/FRIBDAQ/DDASToys).
3. A working knowledge on how to run jobs at NERSC.
4. Installed the Globus SDK and Globus Compute SDK. Both SDKs require Python 3.10 or later; if your OS or containerized RTE does not support Python 3.10, you may need to run under one of the official Docker Python images (or e.g. an Apptainer image built from one of the Docker images) found [here](https://hub.docker.com/_/python). Installation instructions are provided on the Globus SDK and Globus Compute SDK documentation pages. The required packages can also be installed by running `pip install -r requirements.txt` from inside the Python virtual environment.
5. The permissions to write pipeline output on the FRIB DTN.

The analysis flow example contained in this repository uses a combination of transfer and compute action providers to copy FRIB data to NERSC, perform user analysis on the Perlmutter supercomputer, and copy the results back to FRIB. This is done through the FRIB DTN which can communicate with the Globus cloud. A schematic of the data analysis pipeline is shown below, with the steps run using Globus Flows shown inside the blue cloud.

![e21062 Example Flow](images/e21062_flow.png)

### Installing, Configuring, and Running the e21062 Example Flow
- Clone the repository `git clone https://github.com/aschester/flows_e21062.git` somewhere which can mount the Ceph filesystem visible to the FRIB DTN.
- Copy the `globus_flows` directory to NERSC. This directory contains the job scripts which are remotely executed by the compute functions as well as endpoint monitoring tools.
- Open `transfer_compute_mpi.py` and ensure that the collection, endpoint, compute function, and flow UUIDs, and top-level paths are correct. Update the UUIDs and paths as necessary. See the section on [script usage](#usage) for details. The flow will check whether the directory structure defined in `transfer_compute_mpi.py` exists and create it on the remote system if it does not.
- Verify that the endpoint configuration is correct (correct queue, shape of provisioned resources, etc.) and start the compute endpoints at NERSC. If the compute endpoints do not exist, navigate to `globus_flows/ep_launch` and run `create.sh` to create, configure and start the `frib-fit-mpi`, `frib-convert` and `frib-analysis` endpoints.
- (Optional) Turn on the endpoint monitoring. For an experiment, it is a good idea to ask for access to the workflow queue for long-lasting scrontab (Slurm crontab equivalent) jobs. Ensure that the `--dependency=singleton` and `--open-mode=append` options are set for long-running jobs to prevent Slurm from starting multiple instances of the monitor. See the [scrontab documentation](https://docs.nersc.gov/jobs/workflow/scrontab/) for details.
- Run a flow. Note that this must be done from inside the Python virtual environment where the Globus SDK and Globus Compute SDK are installed. The `venvcmd` script provides a shortcut: `./venvcmd ./transfer_compute_mpi.py --rundir /path/to/toplevel/directory/rundir`. You can monitor the status of the flow on the [Globus Web App](https://app.globus.org/runs).
- (Optional) Configure the flow to run automatically. Rather than starting a flow run by hand, it is possible to run the flow in a mode where it will monitor a filesystem on the DTN for new run directories and trigger flows automatically once one is discovered. To watch a directory for events and automatically trigger the flow, run the script as `./venvcmd ./transfer_compute_mpi.py --watchdir /path/to/toplevel/directory`. It may be helpful to background this process and log the output: `nohup ./venvcmd ./transfer_compute_mpi.py --watchdir /path/to/toplevel/directory >> watcher.log 2>&1 &`.

### Usage
This section details the various scripts in this directory and how they are used to setup, configure and run the analysis pipeline as a Globus Flow. The `venvcmd` script is a utility script which allows commands to be executed under the proper Python virtual environment from the native OS on any FRIBDAQ machine.

#### Endpoint Creation and Monitoring
The following scripts in globus_flows/ep_launch/ can be used to setup the compute endpoints, monitor their status, and restart them if necessary. They are intended to be run on the host system of the compute endpoint. The compute endpoints use Parsl's `SlurmProvider` to submit jobs using `sbatch`. The globus_flows/ep_launch/ folder also contains three config-*.yaml files which provide some default configuration for each of the compute endpoints.
- **create.sh**  Create and start compute endpoints named frib-fit-mpi, frib-convert and frib-analysis with the default configurations.
- **delete.py**  Delete all managed compute endpoints. For now, all of the endpoints exist at NERSC. This script makes no effort to determine whether that is always the case and will delete all of the user's managed endpoints.
- **monitor.py**  Monitor the endpoint status and restart any endpoints that are offline. Intended to be run as part of a `scrontab` job.
- **gce**  Wrapper to simplify calls to `globus-compute-endpoint` for endpoints created by create.sh. Example usage: `./gce restart` will restart all of frib-fit-mpi, frib-convert and frib-analysis.

#### Compute Functions
Compute functions support remote execution of FRIBDAQ and user executables under a supported RTE on the NERSC Perlmutter supercomputer. These jobs are run via `sbatch` because the compute endpoints use the Parsl `SlurmProvider`.
- fit_mpi.py: Run batch MPI fitting jobs. Batch submission requires a callback function UUID. To update the callback, run `./venvcmd ./fit_mpi.py --register-callback`. The `function_id` variable within `fit_mpi` must be set using the returned UUID. To re-register the fit function, run `./venvcmd ./fit_mpi.py --register-batch`.
- convert.py: Run batch ROOT-conversion jobs. Batch submission requires a callback function UUID. To update the callback, run `./venvcmd ./convert.py --register-callback`. The `function_id` variable within `convert` must be set using the returned UUID. To re-register the conversion function, run `./venvcmd ./convert.py --register-batch`.
- analyze.py: Run the Liddick group user analysis `betasort` function. This function is called one time per run and uses the `Executor` class to submit the function to Globus. To re-register the function, run `./venvcmd ./analyze.py --register`.

#### Slurm Job Scripts
Scripts in globus_flows/ for remote execution using Globus Compute. These scripts should be installed on the compute host system and are submitted using `sbatch` to the resources allocated by the compute endpoint, see [Endpoint Creation and Monitoring](#endpoint-creation-and-monitoring). The job scripts expect that their input and output directories are mounted to /input and /output in the container image they are run under. Job scripts should write their own logs, as capturing stdout and stderr from Slurm through Parsl is difficult.
- run_compute_fit_mpi.sh: Fit ADC traces and modify the event data using the FRIBDAQ `EventEditor` framework and MPI parallelization. Note that this function uses the version of MPI installed in the FRIBDAQ /usr/opt tree and calls that version's `mpirun` explicitly. 
- run_compute_convert.sh: Convert fitted FRIBDAQ event files to ROOT format using the DDASToys `EEConverter`.
- run_compute_analyze.sh: Perform user analysis. Calls the Liddick group `betasort` executable.

#### Deploy or Update a Flow
Deploy a new flow or update an existing flow. Flow definitions and input schema are found in the transfer/ and transfer_compute/ directories. 
- deploy_flow.py: Deploy or update a flow. Run the script with the `-h` argument to see the options. To update an existing flow, specify its UUID using the `--flowid` argument. 

#### Run a Flow
Scripts which are used to run flows and set a directory-watch trigger for flow automation.
- transfer_compute_mpi.py: Run the analysis flow to transfer data and perform computing tasks remotely at NERSC. Run the script with the `-h` argument to see the options. To start a single flow run by hand, use the `--rundir` option; to start a triggered flow, use the `--watchdir` option. The `--dry-run` option will run the script without running the flow itself. Note that this *does not* validate the input schema, as the `SpecificFlowsClient` does not implement a `dry_run` option like some other Flows clients! The flow definition and input schema are found in transfer_compute/. The flow run by this script is registered under the name FRIB-NERSC-Analysis-Pipeline with UUID babd88e5-d31d-48c7-b3a0-b765389b5c22.
- transfer_resorted.py: Run a flow to transfer data from NERSC to the FRIB DTN. Run the script with the `-h` argument to see the options. Most likely you will only want to override the default paths. The flow definition and input schema are found in transfer/. The flow run by this script is registered under the name FRIB-Transfer with UUID 47557a0b-75ba-4df1-8a85-f5fb556c31a4.
- flows_service.py: Utility functions for interacting with the Globus Flows service, based on flows_service.py found [here](https://github.com/globus/globus-flows-trigger-examples). Utility functions for fetching tokens and authorization as well as creating a Flows Client are provided.
- dirwatch.py: A directory-watching trigger class for automation of the FRIB-NERSC-Analysis-Pipeline flow. Intended to monitor a directory on the FRIB DTN where pipeline input data is copied using the `rsync` command. This is the trigger class used by the FRIB-NERSC-Analysis-Pipeline flow.

#### Testing
Scripts for testing and development on Perlmutter.
- run_compute_fit_mpi.sl: Job submission script for calling run_compute_fit_mpi.sh by hand using `sbatch`. Required arguments are the the run number and segment number e.g. `sbatch run_compute_fit_mpi.sl 1217 0`.
- run_compute_convert.sl: Job submission script for calling run_compute_convert.sh by hand using `sbatch`. Required arguments are the the run number and segment number e.g. `sbatch run_compute_convert.sl 1217 0`.
- run_compute_analyze.sl: Job submission script for calling run_compute_analyze.sh by hand using `sbatch`. Required arguments are the the run number and number of run segments e.g. `sbatch run_compute_analyze.sl 1217 1`. If the number of segments is 0, only the first run segment will be sorted; this is equivalent to specifying the number of segments equal to 1.
- test_fit_mpi.py: A callable test compute function to test parallel fitting using MPI. Must be called from within the proper Python environment. This function is intended for testing and debugging only and is not a registered function which can be called as part of a flow.

## Resources
- [NERSC docs](https://docs.nersc.gov/)
- [Globus Flows](https://docs.globus.org/api/flows/)
- [Globus SDK docs](https://globus-sdk-python.readthedocs.io/en/stable/installation.html)
- [Amazon States Language docs](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html)
- [JSON schema docs](https://json-schema.org/learn/getting-started-step-by-step)
- [Globus Compute](https://www.globus.org/compute)
- [Globus Compute docs (including the SDK)](https://globus-compute.readthedocs.io/en/latest/index.html)
- [Parsl docs](https://parsl.readthedocs.io/en/stable/#)
- [Slurm docs](https://slurm.schedmd.com/)
- The Globus Flows scripts are derived in whole or in part from the [globus-flows-trigger-examples](https://github.com/globus/globus-flows-trigger-examples) repository and are redistributed under the Apache-2.0 license.