# Copilot Chat Dev Setup Scripts

> **NOTE:**  These scripts are currently **for Windows only**.

## Individual Scripts

These scripts take you through each step of the setup process for running Copilot Chat locally.

### 1. Install prerequisites
The first script ensures all requirements are installed using the Chocolatey package manager:
```
.\1_install-reqs.cmd
```

### 2. Start the backend
Before starting the backend, make sure your `appsettings.json` is up to date with the correct endpoints and service specification. You can either store your OpenAI or Azure OpenAI key manually using `dotnet user-secrets`, or let this script do it for you by optionally providing your key as a parameter. 
This script will also generate a localhost developer certificate, and build and run the backend.
```
.\2_init-backend.cmd [KEY]
```

### 3. Start the frontend

The folowing script will generate the `.env` file and start the frontend.
```
.\3_init-frontend.cmd <CLIENT_ID> <TENANT_ID>
```
 Provide your client ID and tenant ID as parameters.
 Alternatively, in place of the tenant ID, you can specify one of the following:
- `common` - for the common endpoint
- `msa` - for the personal MSA tenant
- `msft` - for the Microsoft corporate tenant (internal testing only)



## All-in-One Scripts

Rather than run each script separately, you can use one of these all-in-one solutions to start both the frontend and backend for Copilot Chat with a single command.

As mentioned above, you still need to manually update `appsettings.json` before running these scripts.

### First run
If you are running for the first time, use `start-first-run.cmd`:
```
.\start-first-run.cmd <KEY> <CLIENT_ID> <TENANT_ID>
```
This will run all three of the above scripts to install the prerequisites, store your key, generate the `.env` file, and start both the backend server and frontend app.


### Subsequent runs
If you've previously run Copilot Chat, you can use `start.cmd`. This script does **NOT** install prerequisites and assumes that your key has already been stored in user secrets.

You can optionally provide your client ID and tenant ID as described above. If these arguments are not provided, the script will look for an existing `.env` file to use.

```
.\start.cmd
```
or
```
.\start.cmd <CLIENT_ID> <TENANT_ID>
```
