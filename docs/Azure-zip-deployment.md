<div id="top"></div>

# Azure SDK provisioning 

## Zip deployment using Azure CLI 
<p align="left"><a href="#top">Back to Top</a></p>

With Zip deployment, you can create a .zip package of your function’s files and then publish it directly to Azure by using Azure CLI or Powershell or the zipdeploy REST API (available to the endpoint https://<app_name&gt;.scm.azurewebsites.net/api/zipdeploy).
 
The following steps explains about deploying via Azure CLI.

## Setup Instructions
<p align="left"><a href="#top">Back to Top</a></p>

This document outlines the steps to configure and deploy Python Azure functions with .zip file archives,


  * [Prerequisite](#prerequisite)
  * [Create supporting Azure resources for your function](#create-supporting-azure-resources-for-your-function)
    + [Step 1: Sign in to Azure](#step-1-sign-in-to-azure)
    + [Step 2: Variable declaration](#step-2-variable-declaration)
    + [Step 3: Create a Resource group](#step-3-create-a-resource-group)
    + [Step 4: Create an Azure storage account in the resource group](#step-4-create-an-azure-storage-account-in-the-resource-group)
        + [Step 4.1: Create a storage container in the Azure storage account to store config files](#step-41-create-a-storage-container-in-the-azure-storage-account-to-store-config-files)
        + [Step 4.2: Upload Config Files to the storage container](#step-42-upload-config-files-to-the-storage-container)
    + [Step 5: Create a serverless python function app in the resource group](#step-5-create-a-serverless-python-function-app-in-the-resource-group)
    + [Step 6: Update the function app's settings to connect to the storage accounts](#step-6-update-the-function-app-s-settings-to-connect-to-the-storage-accounts)
      - [Step 6.1: Configure function app settings to connect to the storage account that receives input data](#step-61-configure-function-app-settings-to-connect-to-the-storage-account-that-receives-input-data)
      - [Step 6.2: Configure function app settings to connect to the storage account that contains the config files](#step-62-configure-function-app-settings-to-connect-to-the-storage-account-that-contains-the-config-files)
  * [Create an Azure Cosmos Core (SQL) API serverless account, database and container using Azure CLI](#create-an-azure-cosmos-core-sql-api-serverless-account-database-and-container-using-azure-cli)
    + [Step 1: Declare Variables](#step-1-declare-variables)
    + [Step 2: Create a new Azure Cosmos DB database account](#step-2-create-a-new-azure-cosmos-db-database-account)
    + [Step 3: Create an SQL database under an Azure Cosmos DB account](#step-3-create-an-sql-database-under-an-azure-cosmos-db-account)
    + [Step 4: Create an SQL container under an Azure Cosmos DB SQL database](#step-4-create-an-sql-container-under-an-azure-cosmos-db-sql-database)
    + [Step 5: Update the function app's settings to connect to the Azure Cosmos DB](#step-5-update-the-function-app-s-settings-to-connect-to-the-azure-cosmos-db)
      - [Step 5.1: Get the Azure Cosmos DB Connection string](#step-51-get-the-azure-cosmos-db-connection-string)
      - [Step 5.2: Configure function app settings to use the Azure Cosmos DB connection string](#step-52-configure-function-app-settings-to-use-the-azure-cosmos-db-connection-string)
  * [Package and Publish the code base](#package-and-publish-the-code-base)
    + [Step 1: GIT Clone the Repo](#step-1-git-clone-the-repo)
    + [Step 2: Create function.json in cloud_modules_azure](#step-2-create-functionjson-in-cloud-modules-azure)
    + [Step 3: Package the code base](#step-3-package-the-code-base)
    + [Step 4: Publish the function on Azure using the ZIP package](#step-4-publish-the-function-on-azure-using-the-zip-package)

##  Prerequisite
<p align="left"><a href="#top">Back to Top</a></p>

1. Install Azure CLI using the steps mentioned in https://docs.microsoft.com/en-us/cli/azure/install-azure-cli


2. Git Clone the repo

    ```bash
    git clone <repo url>
    ```

3. cd to the repo directory

    ```bash
    cd <datastream-sdk>
    ```

4. Create a branch and make changes in the branch

    ```bash
    git checkout -b <branch-name>
    ```

5. Follow this document to create the configuration files customised for your stream, 
[Config files Setup Reference](config-setup.md)

##  Create supporting Azure resources for your function 
<p align="left"><a href="#top">Back to Top</a></p>

Create supporting Azure resources for your function
Before you can deploy your function code to Azure, you need to create three resources:

- A _Resource group_, which is a logical container for related resources.
- A _Storage account_, which maintains state and other information about your projects.
- A _function app_, which provides the environment for executing your function code. A function app maps to your local function project and lets you group functions as a logical unit for easier management, deployment, and sharing of resources.

###  Step 1: Sign in to Azure 
<p align="left"><a href="#top">Back to Top</a></p>

If you don't have an Azure subscription, create an Azure free account before you begin.

Cloud Shell is automatically authenticated under the initial account signed-in with. 

```
az login
```

...or use the following command to sign in using a different subscription, replacing <Subscription ID> with your Azure Subscription ID.

```bash
# add subscription here
subscription="<subscriptionId>" 

az account set -s $subscription 
```

###  Step 2: Variable declaration 
<p align="left"><a href="#top">Back to Top</a></p>

Declare variables like, 
- the Azure region where to deploy the function, 
- the Resource Group to use (or create), 
- the Storage Account to create, 
- the name of the Azure Function and 
- the full path of the .zip archive to deploy 
- ... etc

```bash
# Set Azure Region
location="eastus"

# Set Resource group name
resourceGroupName="MDC_DEVTEST_EUS"

# Set Storage account name
# Storage account name must be between 3 and 24 characters 
# in length and use numbers and lower-case letters only.
# This storage account will be used to store function app data
# and configs
storageAccountName="ds2teststorage"
metadataContainerName="configs"

# Storage account name and container holding the 
# input data files
dataStorageAccountName="ds2teststorage"
dataStorageContainer="data"

# Standard_LRS specifies a general-purpose storage account, 
# which is supported by Functions.
skuStorage="Standard_LRS"

# The functions app version.
functionsVersion="4"

# python version
# Allowed values: 3.7, 3.8, and 3.9
pythonVersion="3.9" 

# Function Name
functionAppName="ds2testfunction"

```


###  Step 3: Create a Resource group 
<p align="left"><a href="#top">Back to Top</a></p>

Create a resource group in the region if it doesn't exists

```bash
echo "creating Resource group[$resourceGroupName] in location[$location] if it doesn't exists"
az group exists -g  $resourceGroupName || az group create \
    --name $resourceGroupName \
    --location $location
```

###  Step 4: Create an Azure storage account in the resource group 
<p align="left"><a href="#top">Back to Top</a></p>

Create a general-purpose storage account in your resource group and region

```bash
echo "creating an Azure storage account[$storageAccountName] in the resource group[$resourceGroupName]"
az storage account create \
    --name $storageAccountName \
    --resource-group $resourceGroupName \
    --location $location \
    --sku $skuStorage
```

At this point we are good to create a container and upload the config files

###  Step 4.1: Create a storage container in the Azure storage account to store config files 


Create a storage container in a storage account.

```bash
echo "creating container[$metadataContainerName] in storage account[$storageAccountName]"
az storage container create \
    --name $metadataContainerName \
    --account-name $storageAccountName
```

###  Step 4.2: Upload Config Files to the storage container 

After git clone, 

```bash
echo "uploading configs to container[$metadataContainerName] in storage account[$storageAccountName]"
az storage blob upload-batch \
    --account-name $storageAccountName \
    --destination $metadataContainerName \
    --source "configs" \
    --overwrite
```

###  Step 5: Create a serverless python function app in the resource group 
<p align="left"><a href="#top">Back to Top</a></p>

```bash
az functionapp create \
    --name $functionAppName \
    --storage-account $storageAccountName \
    --consumption-plan-location "$location" \
    --resource-group $resourceGroupName \
    --os-type linux \
    --runtime python \
    --runtime-version $pythonVersion \
    --functions-version $functionsVersion
```

###  Step 6: Update the function app's settings to connect to the storage accounts 
<p align="left"><a href="#top">Back to Top</a></p>

####  Step 6.1: Configure function app settings to connect to the storage account that receives input data

1. Get/Copy the storage account connection string for the storage account.

    ```bash
    storageConnectionString=$(az storage account show-connection-string \
        --name $dataStorageAccountName \
        --resource-group $resourceGroupName \
        --query connectionString \
        --output tsv)
    echo $storageConnectionString
    ```

2. Set `AzureDataStorageConnectionString`

    ```bash
    az functionapp config appsettings set \
        --resource-group $resourceGroupName \
        --name $functionAppName \
        --settings "AzureDataStorageConnectionString=$storageConnectionString"
    ```

####  Step 6.2: Configure function app settings to connect to the storage account that contains the config files

1. Get the storage account connection string

    ```bash
    connstr=$(az storage account show-connection-string \
        --name $storageAccountName \
        --resource-group $resourceGroupName \
        --query connectionString \
        --output tsv)
    echo $connstr
    ```

2. Set `AzureMetadataStorageConnectionString` and `AzureMetadataStorageContainer`

    ```bash
    az functionapp config appsettings set \
        --name $functionAppName \
        --resource-group $resourceGroupName \
        --settings AzureMetadataStorageConnectionString=$connstr AzureMetadataStorageContainer=$metadataContainerName
    ```

##  Create an Azure Cosmos Core (SQL) API serverless account, database and container using Azure CLI 
###  Step 1: Declare Variables 
<p align="left"><a href="#top">Back to Top</a></p>

```bash
cosmosdbAccountName="ds2testdb"
databaseName="ds2db"
cosmosContainerName="ds2cont"
partitionKey="/id"
```
###  Step 2: Create a new Azure Cosmos DB database account 
<p align="left"><a href="#top">Back to Top</a></p>

```bash
az cosmosdb create \
    --name $cosmosdbAccountName \
    --resource-group $resourceGroupName \
    --capabilities EnableServerless \
    --default-consistency-level Eventual \
    --locations regionName="$location" failoverPriority=0 isZoneRedundant=False
```

###  Step 3: Create an SQL database under an Azure Cosmos DB account 
<p align="left"><a href="#top">Back to Top</a></p>

```bash
az cosmosdb sql database create \
    --account-name $cosmosdbAccountName \
    --name $databaseName \
    --resource-group $resourceGroupName
```

###  Step 4: Create an SQL container under an Azure Cosmos DB SQL database 
<p align="left"><a href="#top">Back to Top</a></p>

```bash
az cosmosdb sql container create \
    --resource-group $resourceGroupName \
    --account-name $cosmosdbAccountName \
    --database-name $databaseName \
    --name $cosmosContainerName \
    --partition-key-path $partitionKey
```

###  Step 5: Update the function app's settings to connect to the Azure Cosmos DB 
<p align="left"><a href="#top">Back to Top</a></p>

####  Step 5.1: Get the Azure Cosmos DB Connection string 

```bash
connstr=$(az cosmosdb keys list \
    --name $cosmosdbAccountName \
    --resource-group $resourceGroupName \
    --type connection-strings \
    --query 'connectionStrings[0].connectionString' \
    --output tsv)
echo $connstr
```

####  Step 5.2: Configure function app settings to use the Azure Cosmos DB connection string 

```bash
az functionapp config appsettings set \
    --name $functionAppName \
    --resource-group $resourceGroupName \
    --setting AzureCosmosDBConnectionString=$connstr
```


##  Package and Publish the code base
<p align="left"><a href="#top">Back to Top</a></p>

Refer [Azure-Functions -> Python -> Folder structure](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Cazurecli-linux%2Capplication-level#folder-structure)  for the recommended folder structure for a Python Functions project.

###  Step 1: GIT Clone the Repo
<p align="left"><a href="#top">Back to Top</a></p>

Ignore the following steps if the repo is already clonned.

1. clone the repo

    ```bash
    git clone <repo url>
    ```

2. cd to the directory

    ```bash
    cd <datastream-sdk>
    ```

3. create a branch and make changes in the branch

    ```bash
    git checkout -b <branch-name>
    ```

###  Step 2: Create function.json in cloud_modules_azure
<p align="left"><a href="#top">Back to Top</a></p>

Create/Update `cloud_modules_azure/function.json` with the below input and output bindings.

These are the minimum details needed in function.json

```json
cat << EOF > cloud_modules_azure/function.json
{
    "scriptFile": "__init__.py",
    "entryPoint": "main",
    "bindings": [
        {
            "name": "myblob",
            "type": "blobTrigger",
            "direction": "in",
            "path": "$dataStorageContainer/{name}",
            "connection": "AzureDataStorageConnectionString"
        },
        {
            "type": "cosmosDB",
            "direction": "out",
            "name": "resultdoc",
            "databaseName": "$databaseName",
            "collectionName": "$cosmosContainerName",
            "createIfNotExists": "true",
            "connectionStringSetting": "AzureCosmosDBConnectionString"
        }
    ]
}
EOF
```
###  Step 3: Package the code base
<p align="left"><a href="#top">Back to Top</a></p>

1. Declare variable

    ```bash
    sourceZipPath="ds_code-base.zip" 
    ```

2. Zip the following code base modules to create a deployement package say `$sourceZipPath`.

    ```bash
    rm $sourceZipPath
    zip -r -g $sourceZipPath requirements.txt
    zip -r -g $sourceZipPath host.json
    zip -r -g $sourceZipPath run_aggregations.py
    zip -r -g $sourceZipPath cloud_modules_azure
    zip -r -g $sourceZipPath aggregation_modules
    ```

3. To check the contents of the zip, 

    ```bash
    unzip -l $sourceZipPath
    ```
    
    Sample Output, 
    ```bash
    % unzip -l $sourceZipPath
    Archive:  ds_code-base.zip
      Length      Date    Time    Name
    ---------  ---------- -----   ----
          277  04-22-2022 17:38   requirements.txt
          342  05-19-2022 22:06   host.json
         3658  04-29-2022 11:10   run_aggregations.py
            0  05-19-2022 22:01   cloud_modules_azure/
          607  05-19-2022 22:14   cloud_modules_azure/function.json
           27  04-20-2022 14:47   cloud_modules_azure/requirements.txt
          565  05-19-2022 19:50   cloud_modules_azure/__init__.py
         4920  05-19-2022 20:50   cloud_modules_azure/utils.py
            0  05-19-2022 22:01   aggregation_modules/
         3287  04-26-2022 20:56   aggregation_modules/stream_parser.py
         9649  05-17-2022 10:22   aggregation_modules/aggregator.py
            0  04-26-2022 18:20   aggregation_modules/__init__.py
         6403  04-26-2022 20:49   aggregation_modules/custom_functions.py
         6665  05-05-2022 22:16   aggregation_modules/utils.py
         3484  04-26-2022 20:54   aggregation_modules/provision_parser.py
    ---------                     -------
        39884                     15 files
    ```

###  Step 4: Publish the function on Azure using the ZIP package 

<p align="left"><a href="#top">Back to Top</a></p>

```bash
echo "Publishing zip file[$sourceZipPath] to function App[$functionAppName] in resource[$resourceGroupName]"

az functionapp deployment source config-zip \
    --resource-group $resourceGroupName \
    --name $functionAppName \
    --src $sourceZipPath \
    --timeout 600 \
    --build-remote true \
    --verbose
```

# Reference 
<p align="left"><a href="#top">Back to Top</a></p>

- [Azure - App Service pricing](https://azure.microsoft.com/en-in/pricing/details/app-service/linux)
- [Zip deployment for Azure Functions](https://docs.microsoft.com/en-us/azure/azure-functions/deployment-zip-push)
    - [Python Functions project  - Folder structure](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=asgi%2Cazurecli-linux%2Capplication-level#folder-structure)
- [Quickstart: Create a Python function in Azure from the command line](https://docs.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python?tabs=azure-cli%2Cbash%2Cbrowser)
- [Create a Function App in an App Service plan](https://docs.microsoft.com/en-us/azure/azure-functions/scripts/functions-cli-create-app-service-plan)
- [Create an Azure Cosmos Core (SQL) API serverless account, database and container using Azure CLI](https://docs.microsoft.com/en-us/azure/cosmos-db/scripts/cli/sql/serverless)
- [Azure Command-Line Interface (CLI) documentation](https://docs.microsoft.com/en-us/cli/azure/?view=azure-cli-latest)
    - [az functionapp deployment source config-zip](https://docs.microsoft.com/en-us/cli/azure/functionapp/deployment/source?view=azure-cli-latest#az-functionapp-deployment-source-config-zip)
    - [az cosmosdb](https://docs.microsoft.com/en-us/cli/azure/cosmosdb?view=azure-cli-latest)
- [azure.storage.blob package](https://azuresdkdocs.blob.core.windows.net/$web/python/azure-storage-blob/12.12.0/azure.storage.blob.html#)
