<div id="top"></div>

# DS2 Dashboard

## Table of Contents

* [About The Project](#about-the-project)
* [Features](#features)
* [Input](#input)
* [Sample Output](#sample-output)
* [How to clone the GIT repo](#how-to-clone-the-git-repo)
* [Code Structure](#code-structure)
    + [More Details](#more-details)
* [Configuration Files](#configuration-files)
    + [all_datastream2_fields.json](#all_datastream2_fieldsjson)
    + [all_custom_functions.json](#all_custom_functionsjson)
    + [stream.json](#streamjson)
    + [provision.json](#provisionjson)
* [Configuration File Setup](#configuration-file-setup)
* [Script Usage](#script-usage)
* [Testing with an Input file locally](#testing-with-an-input-file-locally)
* [How to setup in AWS](#how-to-setup-in-aws)
* [How to setup in Azure](#how-to-setup-in-azure)

## About The Project
<p align="left"><a href="#top">Back to Top</a></p>

To empower DS2 customers and create a value to the data delivered to customer object store(S3), business value driven SDK/Package is provided to customer to run on a serverless function (Lambda, Azure functions) and derive metrics to various destination like cloudwatch, SNS, DyanoDB, CosmosDB etc..

Built With

* python3.8
* pandas
* httpagentparser


##  Features 
<p align="left"><a href="#top">Back to Top</a></p>

1. Derive metrics from DS2 Logs uploaded to AWS S3 or Azure blob Storage
2. Supportability DS2 formats
   - JSON
   - STRUCTURED

## Input
<p align="left"><a href="#top">Back to Top</a></p>

Reads Structured(CSV) or JSON format input files produced from DataStream 2.
## Sample Output
<p align="left"><a href="#top">Back to Top</a></p>

Generates the following aggregated Output of the selected fields per file

```json
[
  {
    "start_timestamp": 1606768500,
    "bytes_max": 3241.0,
    "bytes_sum": 97230.0,
    "bytes_count": 30.0,
    "objsize_min": 10.0,
    "objsize_max": 10.0,
    "objsize_sum": 300.0,
    "objsize_count": 30.0,
    "uncompressedsize_sum": 3000.0,
    "transfertimemsec_sum": 60.0,
    "totalbytes_min": 3241.0,
    "totalbytes_max": 3241.0,
    "totalbytes_sum": 97230.0,
    "totalbytes_mean": 3241.0,
    "tlsoverheadtimemsec_min": 0.0,
    "tlsoverheadtimemsec_max": 0.0,
    "total_hits": 42,
    "hits_2xx": 25,
    "hits_3xx": 1,
    "hits_4xx": 1,
    "hits_5xx": 2,
    "traffic_volume": 97230,
    "cache_hit": 24,
    "cache_miss": 6,
    "offload_rate": 80.0,
    "origin_response_time": 0,
    "os": {
      "Windows": 30
    },
    "browser": {
      "Chrome": 30
    },
    "platform": {
      "Windows": 30
    }
  }
]
```

## How to clone the GIT repo
<p align="left"><a href="#top">Back to Top</a></p>

Clone the repo,

```sh
git clone <repo url>
```

Reference - https://www.atlassian.com/git/tutorials/setting-up-a-repository/git-clone

## Code Structure
<p align="left"><a href="#top">Back to Top</a></p>

<table>
<thead>
<tr align="left" valign="top">
    <th>File/Module</th>
    <th>Description</th>
</tr>
</thead>
<tbody>
<tr align="left" valign="top">
    <th><i>run_aggregation.py</i></th>
    <td>Main module that is invoked to aggregate of the input data file </td>
</tr>
<tr align="left" valign="top">
    <th><i>/aggregation_modules</i></th>
    <td>Modules for data aggregation</td>
</tr>
<tr align="left" valign="top">
    <th><i>/cloud_modules_*</i></th>
    <td>
    Utilities to interact with respective cloud services. Say,
    <ul>
    <li> <b><i>/cloud_modules_aws:</i></b> Utilities to interact with aws S3 storage
    <li> <b><i>/cloud_modules_azure:</i></b> Utilities to interact with Azure Blob storage
    </ul>
    </td>
</tr>
<tr align="left" valign="top">
    <th><i>/configs</i></th>
    <td>contains sample configuration files</td>
</tr>
<tr align="left" valign="top">
    <th><i>/frontend_modules/provision_ui</i></th>
    <td> UI framework using Django that helps to create <code>provision.json</code> file containing the list of selected metrics for aggregation.  </td>
</tr>
<tr align="left" valign="top">
    <th><i>/tools</i></th>
    <td>Contains standalone tools that can be used to setup other services on cloud that helps in analysing Datastream data. <br> Example, 
    <ul>
    <li> <b><i>tools/athena:</i></b> To setup Athena in AWS that helps in querying the Datastream 2 data directly from S3 buckets.
    </ul>
    </td>
</tr>
</tbody>
</table>

 ### More Details

After git clone cd to the repository directory and start the pydoc server to get more details on the code base.

```
python -m pydoc -b .
```

## Configuration Files 
<p align="left"><a href="#top">Back to Top</a></p>

The following are the details on the list of input configuration files used by this package

+ [all_datastream2_fields.json](#all_datastream2_fieldsjson)
+ [all_custom_functions.json](#all_custom_functionsjson)
+ [stream.json](#streamjson)
+ [provision.json](#provisionjson)

### all_datastream2_fields.json

1. This JSON file consists of all dataset Fields available in datastream 
2. Example
```json
{
    [...]
	"2003": {
		"name": "objSize",
		"cname": "Object size",
		"dtype": "bigint",
		"agg": [
			"min", "max", "sum", 
		]
	},
    [...]
}
```
3. This file contains the following details,

    <table>
    <tbody>
    <tr align="left" valign="top">
    <th><i>field id</i></th>
    <td>The field id (say, <code>"2003"</code>) corresponds to the the <code>datasetFieldId</code> in stream.json file. </td>
    </tr>
    <tr align="left" valign="top">
    <th><i>"name"</i></th>
    <td></td>
    </tr>
    <tr align="left" valign="top">
    <th><i>"dtype"</i></th>
    <td>data type of the field</td>
    </tr>
    <tr align="left" valign="top">
    <th><i>"cname"</i></th>
    <td>field description </td>
    </tr>
    <tr align="left" valign="top">
    <th><i>"agg"</i></th>
    <td>
        <ul>
        <li> The <code>"agg"</code> tag consists of the list of aggregate functions that can be supported by this field, provided that field is selected in <code>stream_json</code> file. </li> 
        <li> Thus removing it from <code>"agg"</code> list disables the function for that field. </li> 
        <li> Reference: <a href="https://pandas.pydata.org/docs/reference/frame.html"> Pandas > DataFrame > API Reference </a> </li>
        <li> Following are the currently supported functions,
            <table>
                <tbody>
                    <tr align="left" valign="top">
                        <th> <i> min </i> </th>
                        <td> Return the minimum of the values over the requested axis. </td>
                    </tr>
                    <tr align="left" valign="top">
                        <th> <i> max </i> </th>
                        <td> Return the maximum of the values over the requested axis. </td>
                    </tr>
                    <tr align="left" valign="top">
                        <th> <i> sum </i> </th>
                        <td> Return the sum of the values over the requested axis. </td>
                    </tr>
                    <tr align="left" valign="top">
                        <th> <i> count </i> </th>
                        <td> Count non-NA cells for each column or row. </td>
                    </tr>
                    <tr align="left" valign="top">
                        <th> <i> mean </i> </th>
                        <td> Return the mean of the values over the requested axis. </td>
                    </tr>
                    <tr align="left" valign="top">
                        <th> <i> median </i> </th>
                        <td> Return the median of the values over the requested axis. </td>
                    </tr>
                    <tr align="left" valign="top">
                        <th> <i>var </i> </th>
                        <td> Return unbiased variance over requested axis. </td>
                    </tr>
                    <tr align="left" valign="top">
                        <th> <i> any </i> </th>
                        <td> Returns False unless there is at least one element within a series or along a Dataframe axis that is True or equivalent (e.g. non-zero or non-empty) </td>
                    </tr>
                    <tr align="left" valign="top">
                        <th> <i> unique_counts </i> </th>
                        <td> Returns json containing counts of unique rows in the DataFrame.</br>
                        Example for column <code>country</code> it returns,
                        <pre>
    "country": {
      "US": 42
    },
                        </pre>
                        </td>
                    </tr>
                </tbody>
            </table>
            </li>
        </ul>

    </td>
    </tr>
    </tbody>
    </table>

4. Sample File is stored in: `configs/all_datastream2_fields.json`
5. This is a common file and updated only when new fields are added to the datastream. 


### all_custom_functions.json

1. This JSON file contains the list of all the available custom functions that can be selected to aggregate the data.
    <details>
    <summary>Example</summary>

    ```json
    {
        [...]
        "get_status_code_level_hit_counts": {
            "required-fields": [
                "statuscode"
            ],
            "description": "Show Stat Count of HTTP requests"
        },
        [...]
    }
    ```
    </details>

2. This file contains the following details,

    <table>
    <tr align="left" valign="top">
        <th><i>function name</i></th>
        <td> unique name for the function</td>
    </tr>
    <tr align="left" valign="top">
        <th><i>"description"</i></th>
        <td> Short description of this function</td>
    </tr>
    <tr align="left" valign="top">
        <th><i>"required-fields"</i></th>
        <td>dataset field names (in lowercase) from <code>all_datastream2_fields.json</code> that are required to derive this function.</td>
    </tr>
    </table>

3. Sample File is stored in: `configs/all_custom_functions.json`
4. This is a common file and updated only when new functions are added to the datastream. 
5. Following are the list of current available custom functions and their recommended Memory, 

    <table>
        <thead>
            <tr align="left" valign="top">
                <th>custom function</th>
                <th>Required DS2 fields</th>
                <th>Recommended Memory</th>
                <th>Sample Output </th>
            </tr>
        </thead>
        <tbody>
            <tr align="left" valign="top">
                <th><i> get_total_hits </i> </th>
                <td>  </td>
                <td> > 512 MB</td>
                <td>
                    <pre> 
    "total_hits": 42,
                    </pre>
                </td>
            </tr>
            <tr align="left" valign="top">
                <th><i> get_traffic_volume </i> </th>
                <td> totalbytes </td>
                <td> > 512 MB</td>
                <td>
                    <pre> 
    "traffic_volume": 145964, 
                    </pre>
                </td>
            </tr>
            <tr align="left" valign="top">
                <th><i>get_status_code_level_hit_counts </i> </th>
                <td>statuscode</td>
                <td> > 512 MB</td>
                <td>
                    <pre> 
    "hits_2xx": 42,
    "hits_3xx": 0,
    "hits_4xx": 0,
    "hits_5xx": 0,
                    </pre>
                </td>
            </tr>
            <tr align="left" valign="top">
                <th> <i> get_cachestatus </i> </th>
                <td> cachestatus </td>
                <td> > 512 MB</td>
                <td>
                    <pre>
    "cache_hit": 42,
    "cache_miss": 0,
                    </pre>
                </td>
            </tr>
            <tr align="left" valign="top">
                <th> <i> get_offload_rate </i> </th>
                <td> cachestatus </td>
                <td> > 512 MB</td>
                <td>
                    <pre> 
    "offload_rate": 10.0, 
                    </pre> 
                </td>
            </tr>
            <tr align="left" valign="top">
                <th> <i> get_origin_response_time </i> </th>
                <td> cachestatus, cacherefreshsrc, turnaroundtimemsec </td>
                <td> > 512 MB</td>
                <td>
                    <pre> 
    "origin_response_time": 10, 
                    </pre> 
                </td>
            </tr>
            <tr align="left" valign="top">
                <th> <i> get_user_agent_details </i> </th>
                <td> ua </td>
                <td> > 1024 MB</td>
                <td>
                    <pre>
    "os": {
        "Windows": 30
        },
    "browser": {
        "Chrome": 30
        },
    "platform": {
        "Windows": 30
        },
                    </pre>
                </td>
            </tr>
        </tbody>
    </table>

### stream.json

1. This is a JSON file containing the stream specific details.
2. i.e this file is used to understand the fields configured for this stream.
3. This can be pulled from portal using the steps mentioned [here](docs/config-setup-stream.md)
4. Sample File is stored in: `configs/stream.json`
    - This needs to be updated with the stream specific file.

### provision.json

1. This is a JSON file containing the subset of custom functions that are selected for this stream.
    <details>
    <summary>Example</summary>

    ```json
    {
        "aggregation-interval": 300,
        [...]
        "bytes": [
            "max",
            "sum",
            "count"
        ],
        [...]
        "custom-functions": [
            "get_status_code_level_hit_counts",
            "get_traffic_volume",
            [...]
        ]
    }
    ```
    
    </details>
2. function are triggerred to generate output for these selected aggregate functions for the input files.
3. `"aggregation-interval"`, specifies the time in secs to aggregate the data based on the `Request Time`. 
    - Setting this to `-1` disables time based aggregation.
4. Sample File is stored in: `configs/provision.json`
    - This needs to be updated with the stream specific file.
5. This file can be manually edited or generated using the steps mentioned [here](docs/config-setup-provision.md)

## Configuration File Setup
<p align="left"><a href="#top">Back to Top</a></p>

Follow this document to create the config files customised for your stream, 
[Config files Setup Reference](docs/config-setup.md)

## Script Usage
<p align="left"><a href="#top">Back to Top</a></p>

```python
% python run_aggregations.py --help
usage: [...]/run_aggregations.py [-h] [--loglevel {critical,error,warn,info,debug}]
                                                                [--input INPUT]

Helps aggregate data

options:
  -h, --help            show this help message and exit
  --loglevel {critical,error,warn,info,debug}
                        logging level.
                        (default: info)
                        
  --input INPUT         specify the input file to aggregate.
                        (default: /[...]/sample-input/test-data-custom.gz)
```

## Testing with an Input file locally
<p align="left"><a href="#top">Back to Top</a></p>

Before setting up in the cloud server, this can be tested locally to ensure the aggregated output is as expected as below. 
- Ensure to update the configs as needed in `configs/` directory
- The custom input file can be specified via `--input` option to run this.
- Ensure the output generated is as expected.
<details>
  <summary>Example</summary>

```bash
% python run_aggregations.py --input sample-input/test-data-custom.gz
Result...
[
  {
    "start_timestamp": 1606768500,
    "bytes_max": 3241.0,
    "bytes_sum": 97230.0,
    "bytes_count": 30.0,
    "objsize_min": 10.0,
    "objsize_max": 10.0,
    "objsize_sum": 300.0,
    "objsize_count": 30.0,
    "uncompressedsize_sum": 3000.0,
    "transfertimemsec_sum": 60.0,
    "totalbytes_min": 3241.0,
    "totalbytes_max": 3241.0,
    "totalbytes_sum": 97230.0,
    "totalbytes_mean": 3241.0,
    "tlsoverheadtimemsec_min": 0.0,
    "tlsoverheadtimemsec_max": 0.0,
    "tlsoverheadtimemsec_sum": 0.0,
    "total_hits": 30,
    "hits_2xx": 25,
    "hits_3xx": 1,
    "hits_4xx": 1,
    "hits_5xx": 2,
    "traffic_volume": 97230,
    "cache_hit": 24,
    "cache_miss": 6,
    "offload_rate": 80.0,
    "origin_response_time": 0,
    "os": {
      "Windows": 30
    },
    "browser": {
      "Chrome": 30
    },
    "platform": {
      "Windows": 30
    }
  }
]
```
</details>

## How to setup in AWS
<p align="left"><a href="#top">Back to Top</a></p>

Follow this document for detailed setup instructions on AWS, 
[AWS Setup Reference](docs/AWS-setup.md)

## How to setup in Azure
<p align="left"><a href="#top">Back to Top</a></p>

Follow this document for detailed setup instructions on Azure, [Azure Setup Reference](docs/Azure-setup.md)
