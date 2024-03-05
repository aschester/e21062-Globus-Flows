# Automated Data Analysis Using Globus Flows
A. Chester  
Facility for Rare Isotope Beams  
640 S. Shaw Ln.  
East Lansing, MI 48924 USA  

5 March 2024  

## Introduction
This repository contains an automated workflow example for FRIB data analysis used during FDSi experiment e21062B (PI: H. Crawford) which ran 27 Feb. to 4 Mar. 2024. The workflow utilizes the computational resources available at NERSC to increase the throughput for compute-intensive tasks such as fitting ADC trace data. High-speed data transfer between FRIB and NERSC is done over ESnet, and the entire workflow--data transfer and analysis--is managed using a Globus Flow. Some familiarity with Globus, HPC computing (specifically at NERSC), and the e21062 analysis methods are assumed, though the overall framework is general enough to apply to other use cases.

### Globus Flows
A Globus Flow is composed of a series of _action providers_, which perform _actions_ as part of a _flow_. The service to run a file transfer between Globus collections is an example of an action provider. The associated action contains the results, status, and metadata associated with a particular invocation of the transfer action provider. A flow is a single operation which incorporates (possibly many) action providers in a defined order: for example, copying data from a source colletion to a destination colleciton via some intermediary collection. Starting a flow with a particular set of inputs is called a _run_ or _flow run_. A number of action providers are hosted by Globus and can be used to construct custom flows.

### Flow Definitions
A flow _definition_, perhaps unsurprisingly, defines the relationship between the actions of a flow, implemented as a type of state machine. Flow definitions are JSON-formatted files written using a derivative of the Amazon States Language specific to Globus Flows. A simple transfer flow definition could consist of a single transfer action run by the transfer action provider.

### Flow Inputs
The input to a flow is known as an _input document_. Many (if not all) couture flows require custom inputs. A flow's _input schema_ can be used to validate a user's input document. If the input document does not conform to the expected format defined by the input schema, the flow run will not start. Input documents and schema are written in the JSON schema format. Returning to the transfer example above, a transfer flow input schema could require source and destination paths as part of an input document. Any input documents which do not specify these paths are not valid.

### e21062 Example Flow
The e21062 flow contained in this repository uses a combination of transfer and compute action providers to copy FRIB data to NERSC, perform user analysis, and copy the results back to FRIB. This is done through the FRIB DTN which can communicate with the Globus cloud. A schmatic of the flow is shown below.

![e21062 Example Flow](images/e21062_flow.png)