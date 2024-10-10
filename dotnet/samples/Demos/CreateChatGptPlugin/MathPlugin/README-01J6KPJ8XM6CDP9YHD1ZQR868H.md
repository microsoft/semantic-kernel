---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:52:09Z
---

# Semantic Kernel OpenAI plugin starter

This project provides starter code to create a OpenAI plugin. It includes the following components:

- An endpoint that serves up an ai-plugin.json file for ChatGPT to discover the plugin
- A generator that automatically converts prompts into prompt endpoints
- The ability to add additional native functions as endpoints to the plugin

## Prerequisites

- [.NET 6](ht********************************************.0) is required to run this starter.
- [Azure Functions Core Tools](ht****************************************************ls) is required to run this starter.
- Install the recommended extensions
- [C#](ht*********************************************************************rp)
- [Semantic Kernel Tools](ht**********************************************************************************el) (optional)

## Configuring the starter

To configure the starter, you need to provide the following information:

- Define the properties of the plugin in the appsettings.json file.
- Enter the API key for your AI endpoint in the [local.settings.json](./azure-function/local.settings.json.example) file.

### Using appsettings.json

Configure an OpenAI endpoint

1. Copy [settings.json.openai-example](./azure-function/config-samples/appsettings.json.openai-example) to `./appsettings.json`
2. Edit the `kernel` object to add your OpenAI endpoint configuration
3. Edit the `aiPlugin` object to define the properties that get exposed in the ai-plugin.json file

Configure an Azure OpenAI endpoint

1. Copy [settings.json.azure-example](./azure-function/config-samples/appsettings.json.azure-example) to `./appsettings.json`
2. Edit the `kernel` object to add your Azure OpenAI endpoint configuration
3. Edit the `aiPlugin` object to define the properties that get exposed in the ai-plugin.json file

### Using local.settings.json

1. Copy [local.settings.json.example](./azure-function/local.settings.json.example) to `./azure-function/local.settings.json`
2. Edit the `Values` object to add your OpenAI endpoint configuration in the `apiKey` property

## Running the starter

To run the Azure Functions application just hit `F5`.

To build and run the Azure Functions application from a terminal use the following commands:

```powershell {"id":"01J6KPQ08HCTS3Q7KZ3W92WKDF"}
cd azure-function
dotnet build
cd bin/Debug/ne**.0
func host start
```
