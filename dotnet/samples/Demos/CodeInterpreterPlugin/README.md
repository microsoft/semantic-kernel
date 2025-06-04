# Semantic Kernel - Code Interpreter Plugin with Azure Container Apps

This example demonstrates how to do AI Code Interpretetion using a Plugin with Azure Container Apps to execute python code in a container.

## Create and Configure Azure Container App Session Pool  
   
1. Create a new Container App Session Pool using the Azure CLI or Azure Portal.
2. Specify "Python code interpreter" as the pool type.
3. Add the following roles to the user that will be used to access the session pool:
   - The `Azure ContainerApps Session Executor` role to be able to create and manage sessions.
   - The `Container Apps SessionPools Contributor` role to be able to work with files.

## Configuring Secrets

The example require credentials to access OpenAI and Azure Container Apps (ACA)

If you have set up those credentials as secrets within Secret Manager or through environment variables for other samples from the solution in which this project is found, they will be re-used.

### To set your secrets with Secret Manager:

```
dotnet user-secrets init

dotnet user-secrets set "OpenAI:ApiKey" "..."
dotnet user-secrets set "OpenAI:ChatModelId" "gpt-3.5-turbo" # or any other function callable model.

dotnet user-secrets set "AzureContainerAppSessionPool:Endpoint" " .. endpoint .. "
```

### To set your secrets with environment variables

Use these names:

```
# OpenAI
OpenAI__ApiKey
OpenAI__ChatModelId

# Azure Container Apps
AzureContainerAppSessionPool__Endpoint
```

### Usage Example

User: Upload the file c:\temp\code-interpreter\test-file.txt

Assistant: The file test-file.txt has been successfully uploaded.

User: How many files I have uploaded ?

Assistant: You have uploaded 1 file.

User: Show me the contents of this file

Assistant: The contents of the file "test-file.txt" are as follows:

```text
the contents of the file
```