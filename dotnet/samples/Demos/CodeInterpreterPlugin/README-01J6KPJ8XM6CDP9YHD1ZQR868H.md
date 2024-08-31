---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:54:54Z
---

# Semantic Kernel - Code Interpreter Plugin with Azure Container Apps

This example demonstrates how to do AI Code Interpretetion using a Plugin with Azure Container Apps to execute python code in a container.

## Configuring Secrets

The example require credentials to access OpenAI and Azure Container Apps (ACA)

If you have set up those credentials as secrets within Secret Manager or through environment variables for other samples from the solution in which this project is found, they will be re-used.

### To set your secrets with Secret Manager:

```sh {"id":"01J6KPW1GVTA7TMS3JR5BS6DDY"}
dotnet user-secrets init

dotnet user-secrets set "OpenAI:ApiKey" "..."
dotnet user-secrets set "OpenAI:ChatModelId" "gp*********bo" # or any other function callable model.

dotnet user-secrets set "AzureContainerApps:Endpoint" " .. endpoint .. "
```

### To set your secrets with environment variables

Use these names:

```sh {"id":"01J6KPW1GVTA7TMS3JR90XESJN"}
# OpenAI
OpenAI__ApiKey
OpenAI__ChatModelId

# Azure Container Apps
AzureContainerApps__Endpoint
```

### Usage Example

User: Upload the file c:\temp\code-interpreter\test-file.txt

Assistant: The file test-file.txt has been successfully uploaded.

User: How many files I have uploaded ?

Assistant: You have uploaded 1 file.

User: Show me the contents of this file

Assistant: The contents of the file "test-file.txt" are as follows:

```text {"id":"01J6KPW1GVTA7TMS3JRA9N82E0"}
the contents of the file
```