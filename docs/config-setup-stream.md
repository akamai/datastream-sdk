<div id="top"></div>

The following document details about, 

+ [How to pull Stream ID Configs?](#how-to-pull-stream-id-configs)
    * [Summary](#summary)
    * [API Examples](#api-examples)

# How to pull Stream ID Configs?

## Summary
<p align="left"><a href="#top">Back to Top</a></p>

Use the following command to get the respective stream id details and save it to `stream.json`,

```
http --auth-type=edgegrid -a default: -o stream.json ":/datastream-config-api/v1/log/streams/<streamid>"
```

However in order to run this command successfully, set up the required access using the detailed steps mentioned here,
<a href="https://techdocs.akamai.com/developer/docs/set-up-authentication-credentials">Get Started with APIs </a>


Briefly,


1. Install `httpie-edgegrid`,
   ```bash
   python -m pip install httpie-edgegrid
   ```

2. Run this command to verify the installation and check the version:

    ```bash
    pip show httpie-edgegrid
    ```

2. Set up your `/Users/{login}/.edgerc` file. 

    1. If you haven't already, you'll need to [Create authentication credentials](https://techdocs.akamai.com/developer/docs/set-up-authentication-credentials).
    2. The httpie-edgegrid plugin relies on an .edgerc file to authenticate requests. 
    2. If you need help setting up your .edgerc file, refer to [Add credential to .edgerc file](https://techdocs.akamai.com/developer/docs/set-up-authentication-credentials#add-credential-to-edgerc-file)

3. Now we are good to run our APIs. Use the following command to get the respective stream id details and save it to `stream.json`,

    ```bash
    http --auth-type=edgegrid -a default: -o stream.json ":/datastream-config-api/v2/log/streams/{streamId}"
    ```

4. This stream ID file will be copied to `configs/` directory

## API Examples
<p align="left"><a href="#top">Back to Top</a></p>

<table>
    <thead>
    <tr align="left" valign="top">
        <th>
            Reference > <a href="https://techdocs.akamai.com/datastream2/v2/reference/api">DataStream 2 API v2</a>
        </th>
        <th>
            Example
        </th>
    </tr>
    </thead>
    <tbody>
    <tr align="left" valign="top">
        <td valign="top">
            <a href="https://techdocs.akamai.com/datastream2/v2/reference/get-dataset-fields">List data set fields
</a>
        </td>
        <td>
            <code>
                http --auth-type=edgegrid -a default: ":/datastream-config-api/v2/log/datasets-fields"
            </code>
        </td>
    </tr>
    <tr align="left" valign="top">
        <td valign="top">
            <a href="https://techdocs.akamai.com/datastream2/v2/reference/get-streams">List all streams</a>
        </td>
        <td>
            <code>
                http --auth-type=edgegrid -a default: ":/datastream-config-api/v2/log/streams"
            </code>
        </td>
    </tr>
    <tr align="left" valign="top">
        <td valign="top">
            <a href="https://developer.akamai.com/api/core_features/datastream2_config/v1.html#getstream">Get particular stream details</a>
        </td>
        <td>
            <code>
                http --auth-type=edgegrid -a default: ":/datastream-config-api/v2/log/streams/{streamId}"
            </code>
            <br/>
        </td>
    </tr>
    </tbody>
</table>

## References
<p align="left"><a href="#top">Back to Top</a></p>

- [Akamai Developer Tools > Create authentication credentials](https://techdocs.akamai.com/developer/docs/set-up-authentication-credentials)
- [Akamai Developer Tools > HTTPie](https://techdocs.akamai.com/developer/docs/httpie-make-api-calls)
- [DataStream 2 API](https://techdocs.akamai.com/datastream2/reference/api)