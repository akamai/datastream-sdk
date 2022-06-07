<div id="top"></div>

The following document details about, 

+ [How to generate provision.json?](#how-to-generate-provisionjson)
    - [Summary](#summary)
    - [Prerequisite](#prerequisite)
    - [Run the local server](#run-the-local-server)


# How to generate provision.json?

## Summary 
<p align="left"><a href="#top">Back to Top</a></p>

1. provision.json file contains the list of aggregate (min, max, sum etc) and custom functions that are selected for the output. 
2. This file can manually be edited and placed in the configs folder. 
3. Or can be genereted via the following UI tool.

## Prerequisite
<p align="left"><a href="#top">Back to Top</a></p>

1. Git Clone the repo

    ```bash
    git clone <repo url>
    ```

2. cd to the repo directory

    ```
    cd <datastream-sdk>
    ```

3. Create a branch and make changes in the branch

    ```bash
    git checkout -b <branch-name>
    ```

4. Install the required python third-party modules from the requirements files,

    ```python
    python3 -m pip install -r base-requirements.txt -r frontend_modules/requirements.txt
    ```

    - More details - https://docs.djangoproject.com/en/4.0/topics/install/#installing-official-release


5. Pull the stream configuration file using the steps mentioned here - [How to pull Stream ID Configs?](config-setup-stream.md)

## Run the local server
<p align="left"><a href="#top">Back to Top</a></p>

1. cd to the `<repo>/frontend_modules` directory if not already

    ```bash
    cd {datastream-sdk}/frontend_modules
    ```

2. Start the local server using the following command, 

    ```bash
    % python manage.py runserver
    Watching for file changes with StatReloader
    Performing system checks...

    System check identified no issues (0 silenced).
    April 22, 2022 - 17:33:17
    Django version 4.0.3, using settings 'provision_ui.settings'
    Starting development server at http://127.0.0.1:8000/
    Quit the server with CONTROL-C.
    ```

3. Open the provided development server link - http://127.0.0.1:8000/

4. Select the needed fields and Submit in the UI.

5. Once Submitted, this generates `provision.json` file under `configs/` directory with the selected dataset. 

## Reference
<p align="left"><a href="#top">Back to Top</a></p>

-  https://docs.djangoproject.com/en/4.0/topics/install/#installing-official-release