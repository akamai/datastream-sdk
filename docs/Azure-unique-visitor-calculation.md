<div id="top"></div>

# Azure SDK provisioning for unique visitor calculation

## Deployment using Azure Portal

## Setup Instructions
<p align="left"><a href="#top">Back to Top</a></p>

This document outlines the steps to configure and deploy Python Azure functions for unique visitor calculation

<i>Note: Unique Visitor calculation will work only on Azure </i>

## what is unique visitor?

## A unique visitor calculated every day based on user agent and client IP is an estimate of the number of distinct individuals who visit a website over a period of time. It is typically calculated by analyzing the user agent and client IP address data that is recorded in the website's server logs

## How the data get stored in cosmos db for unique visitor calculation?

### Data getting stored in cosmos db for unique visitor calculation based on partition key where partition key = [loglineDate_lastOctetOfClientIP]
```
Example :- 

    id                                        partitionKey              Data

    "0c0a62cf-25e7-454b-b23b-b66977c3a5dc"    "2023-02-25_98"            {
   
                                                                         "partition_key": "2023-02-25_98",
                                                                         "date": "2023-02-25",
                                                                         "last_octet": "98", 
                                                                          ...<<more data>>
                                                                          }

```
## Prerequisite
<p align="left"><a href="#top">Back to Top</a></p>
 
1. Should have two container created in Azure storageAccount
   - first container say `metadata` that will contain config files
   - second container say `data`  that will contain the logline data
2. Should have two cosmos database containers created
   - first cosmos db container say `cosmosdbcontainer1` will be used for out binding for the azure function say `cloud_modules_azure`
   - second cosmos db container say `cosmosdbcontainer2` will be used to store the partitioned data for unique visitor calculation


## Follow below step to setup unique visitor calculation

1. Set <code> aggregation-interval = 86400(seconds)</code> in the configs/provision.json, this will require to calculate the daily unique visitors
2. Deploy the datastream-sdk in Azure by following [Deployment using Azure Portal Reference](Azure-portal-deployment.md)

# Run unique visitor
 - Navigate to **Home > Function App**
 - Go to **Functions**
 - Click on **azure_unique_visitor**
 - Click on **Code + Test**
 - Click on **Test/Run**
 - Click on **Input**
 - Select **HTTP method as POST**
 - Select **Key as master (Host Key)**
 - In the **Body** pass the request body as below:-
    ``` 
       {
         "from_date":"YYYY-MM-DD",
         "to_date":"YYYY-MM-DD"  
       }
       Example:-
       {
         "from_date":"2023-02-21",
         "to_date":"2023-02-22"  
       }
   ```
<i>Note: By default the interval between `from_date` and  `to_date`  90 days. </i>
 - Expected response
  ```
      HTTP response code
      200 OK
      {
       "YYYY-MM-DD" : <<unique visitors count>>
      }
    
      Example:-
      {
      "2023-02-22": 11,
      "2023-02-21": 6
      }
  ```
