# Copilot Chat Dev Setup Scripts

> **NOTE:**  These scripts are currently for Windows only.

The first script ensures all requirements are installed using the Chocolatey package manager:
```
.\1_install-reqs.cmd
```

Before starting the backend, make sure your `appsettings.json` is up to date with the correct endpoints and service specification. You can either store your OpenAI or Azure OpenAI key manually using `dotnet user-secrets`, or let this script do it for you by optionally providing your key as a parameter. 
This script will also generate a localhost developer certificate, and build and run the backend.
```
.\2_init-backend.cmd [KEY]
```

The folowing script will generate the `.env` file and start the front end. Provide your client ID as a parameter, along with `msa` for the personal MSA tenant or `corp` for the Microsoft corporate tenant. If no tenant is specified, `common` will be used.

```
.\3_init-frontend.cmd YOUR_CLIENT_ID [msa|corp]
```