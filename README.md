# Automated Data Analysis Using Globus Flows
A. Chester  
Facility for Rare Isotope Beams  
640 S. Shaw Ln.  
East Lansing, MI 48924 USA  

5 March 2024  

## [Introduction]
This repository contains an automated workflow example for FRIB data analysis used during FDSi experiment e21062B (PI: H. Crawford) which ran 27 Feb. to 4 Mar. 2024. The workflow utilizes the computational resources available at NERSC to increase the throughput for compute-intensive tasks such as fitting ADC trace data. High-speed data transfer between FRIB and NERSC is done over ESnet, and the entire workflow--data transfer and analysis--is managed using a Globus Flow. Some familiarity with Globus, HPC computing (specifically at NERSC), and the e21062 analysis methods are assumed, though the overall framework is general enough to apply to other use cases. The e21062 flow software is written primarily in Python and makes heavy use of the Globus SDK.

## Globus Flows
A Globus Flow is composed of a series of _action providers_, which perform _actions_ as part of a _flow_. The service to run a file transfer between Globus collections is an example of an action provider. The associated action contains the results, status, and metadata associated with a particular invocation of the transfer action provider. A flow is a single operation which incorporates (possibly many) action providers in a defined order: for example, copying data from a source colletion to a destination colleciton via some intermediary collection. Starting a flow with a particular set of inputs is called a _run_ or _flow run_. A number of action providers are hosted by Globus and can be used to construct custom flows.

### Flow Definitions
A flow _definition_, perhaps unsurprisingly, defines the relationship between the actions of a flow, implemented as a type of state machine. Flow definitions are JSON-formatted files written using a derivative of the Amazon States Language specific to Globus Flows. A simple transfer flow definition could consist of a single transfer action run by the transfer action provider.

### Flow Inputs
The input to a flow is known as an _input document_. Many (if not all) couture flows require custom inputs. A flow's _input schema_ can be used to validate a user's input document. If the input document does not conform to the expected format defined by the input schema, the flow run will not start. Input documents and schema are written in the JSON schema format. Returning to the transfer example above, a transfer flow input schema could require source and destination paths as part of an input document. Any input documents which do not specify these paths are not valid.

### Globus Compute
Globus Compute provides a "Function-as-a-Service" (FaaS) platform, allowing user's to execute their code using a remote _compute endpoint_. The endpoint is run by the user and provides an interface which allows for remote function execution on some host system. Resource requirements and scaling are defined as part of the endpoint configuraton. Remote execution of a function is performed by either calling the `.submit()` method of the Globus Compute `Executor` class or using the Globus Compute `Client` batching. Pre-registered functions can be invoked using both of these methods. Parsl is used by the Globus Compute platform to manage resources specified by the endpoint configuration. At NERSC, Parsl must interact with the Slurm scheduler to submit tasks to allocated resources.

### Documentation/Further Reading
- [NERSC](https://docs.nersc.gov/)
- [Globus Flows](https://docs.globus.org/api/flows/)
- [Globus SDK](https://globus-sdk-python.readthedocs.io/en/stable/installation.html)
- [Amazon States Language](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html)
- [JSON schema format](https://json-schema.org/learn/getting-started-step-by-step)
- [Globus Compute](https://funcx.readthedocs.io/en/latest/endpoints.html)
- [Parsl](https://parsl.readthedocs.io/en/stable/#)
- [Slurm](https://slurm.schedmd.com/)

# e21062 Example Flow
The author assumes the user has:
1. An account at NERSC which is part of the e21062 analysis project m4386.
2. Familiarity with the [FRIBDAQ parallel trace fitting software](https://github.com/FRIBDAQ/DDASToys).
3. A working knowledge on how to run jobs at NERSC.
4. Installed the Globus SDK and Globus Compute SDK following the instrucitons on their respective documentation pages. Both SDKs require Python 3.10 or later; if your OS or containerized RTE does not support Python 3.10, you may need to run under one of the offical Docker Python images (or e.g. an Apptainer image built from one of the Docker images) found [here](https://hub.docker.com/_/python).

The `transfer_compute` flow contained in this repository uses a combination of transfer and compute action providers to copy FRIB data to NERSC, perform user analysis on the Perlmutter supercomputer, and copy the results back to FRIB. This is done through the FRIB DTN which can communicate with the Globus cloud. A schmatic of the data analysis pipeline is shown below, with the steps run using Globus Flows shown inside the blue cloud.

![e21062 Example Flow](images/e21062_flow.png)

## Installation
- Clone the repository `git clone https://github.com/aschester/flows_e21062.git` somewhere which can mount the Ceph filesystem visible to the FRIB DTN.
- Open `transfer_compute_mpi.py` and ensure that the endpoint UUIDs, function UUIDs, top-level paths and flow UUID are correct. See 

# [Blah](#blah)
## Blah
blah blah blah