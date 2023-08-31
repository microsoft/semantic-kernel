# Semantic Kernel Node syntax examples

This project contains a collection of examples which demonstrate how to call the Semantic Kernel from
a Node application.

The examples use [node-api-dotnet](https://github.com/microsoft/node-api-dotnet).
This project enables advanced interoperability between .NET and JavaScript in the same process.

To run the samples, first set the following environment variables referencing your
[Azure OpenAI deployment](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart):

``` bash
# Azure OpenAI
set AzureOpenAI__ServiceId=..
set AzureOpenAI__DeploymentName=text-davinci-003
set AzureOpenAI__Endpoint=https://... .openai.azure.com/
set AzureOpenAI__ApiKey=...
```

Then run the following commands in sequence:

``` bash
# Install SemanticKernel nuget packages into the project and generate type definitions.
dotnet build

# Install node-api-dotnet npm package into the project.
npm install

# Run example JS code that uses the above packages to call the Azure OpenAI service.
node Example01_SummarizeText.js
```
