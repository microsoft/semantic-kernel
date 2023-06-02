# Semantic Kernel Service - CopilotChat
This ASP.Net web application exposes the Semantic Kernel through a REST-like interface.

# Configure your environment
Before you get started, make sure you have the following requirements in place:
1. [.NET 6.0](https://dotnet.microsoft.com/en-us/download/dotnet/6.0) for building and deploying .NET 6 projects.
1. Update the properties in `./appsettings.json` to configure your Azure OpenAI resource or OpenAI account.
1. Generate and trust a localhost developer certificate.
   - For Windows and Mac run 
     ```bash
     dotnet dev-certs https --trust`
     ```
     > Select `Yes` when asked if you want to install this certificate.
   - For Linux run 
     ```bash
     dotnet dev-certs https
     ```
   
   > To verify the certificate has been installed and trusted, run `dotnet run dev-certs https --check`

   > To clean your system of the developer certificate, run `dotnet run dev-certs https --clean`

1. **(Optional)** [Visual Studio Code](http://aka.ms/vscode) or [Visual Studio](http://aka.ms/vsdownload).

# Start the WebApi Service
You can start the WebApi service using the command-line, Visual Studio Code, or Visual Studio.
## Command-line
1. Open a terminal
1. Change directory to the Copilot Chat webapi project directory.
   ```
   cd semantic-kernel/samples/apps/copilot-chat-app/webapi
   ```
1. (Optional) Build the service and verify there are no errors.
   ```
   dotnet build
   ```
1. Run the service
   ```
   dotnet run
   ```
1. Early in the startup, the service will provide a probe endpoint you can use in a web browser to verify
   the service is running.
   ```
   info: Microsoft.SemanticKernel.Kernel[0]
         Health probe: https://localhost:40443/probe
   ```

## Visual Studio Code
> TODO: pending the addition of `./.vscode/tasks.json`

## Visual Studio (2022 or newer)
1. Open the solution file in Visual Studio 2022 or newer (`semantic-kernel/dotnet/SK-dotnet.sln`).
1. In the solution explorer expand the `samples` folder.
1. Right-click on the `CopilotChatApi` and select `Set as Startup Project`.
1. Start debugging by pressing `F5` or selecting the menu item `Debug`->`Start Debugging`.

# (Optional) Enabling the Qdrant Memory Store
By default, the service uses an in-memory volatile memory store that, when the service stops or restarts, forgets all memories.
[Qdrant](https://github.com/qdrant/qdrant) is a persistent scalable vector search engine that can be deployed locally in a container or [at-scale in the cloud](https://github.com/Azure-Samples/qdrant-azure).

To enable the Qdrant memory store, you must first deploy Qdrant locally and then configure the Copilot Chat API service to use it.

## 1. Configure your environment
Before you get started, make sure you have the following additional requirements in place:
- [Docker Desktop](https://www.docker.com/products/docker-desktop) for hosting the [Qdrant](https://github.com/qdrant/qdrant) vector search engine.

## 2. Deploy Qdrant VectorDB locally 
1. Open a terminal and use Docker to pull down the container image.
    ```bash
    docker pull qdrant/qdrant
    ```

1. Change directory to this repo and create a `./data/qdrant` directory to use as persistent storage. 
    Then start the Qdrant container on port `6333` using the `./data/qdrant` folder as the persistent storage location.
   
    ```bash
    cd /src/semantic-kernel
    mkdir ./data/qdrant
    docker run --name copilotchat -p 6333:6333 -v "$(pwd)/data/qdrant:/qdrant/storage" qdrant/qdrant
    ```
    > To stop the container, in another terminal window run `docker container stop copilotchat; docker container rm copilotchat;`.

# (Optional) Enable Application Insights telemetry

Enabling telemetry on CopilotChatApi allows you to capture data about requests to and from the API, allowing you to monitor the deployment and monitor how the application is being used.

To use Application Insights, first create an instance in your Azure subscription that you can use for this purpose.

On the resource overview page, in the top right use the copy button to copy the Connection String and paste this into the `APPLICATIONINSIGHTS_CONNECTION_STRING` setting as either a appsettings value, or add it as a secret.

In addition to this there are some custom events that can inform you how users are using the service such as `SkillFunction`.

To access these custom events the suggested method is to use Azure Data Explorer (ADX). To access data from Application Insights in ADX, create a new dashboard and add a new Data Source (use the elipsis dropdown in the top right).

In the Cluster URI use the following link: `https://ade.applicationinsights.io/subscriptions/<Your subscription Id>`. The subscription id is shown on the resource page for your Applications Insights instance. You can then select the Database for the Application Insights resource.

For more info see [Query data in Azure Monitor using Azure Data Explorer](https://learn.microsoft.com/en-us/azure/data-explorer/query-monitor-data).

CopilotChat specific events are in a table called `customEvents`.

For example to see the most recent 100 skill function invocations:

```kql
customEvents
| where timestamp between (_startTime .. _endTime)
| where name == "SkillFunction"
| extend skill = tostring(customDimensions.skillName)
| extend function = tostring(customDimensions.functionName)
| extend success = tobool(customDimensions.success)
| extend userId = tostring(customDimensions.userId)
| extend environment = tostring(customDimensions.AspNetCoreEnvironment)
| extend skillFunction = strcat(skill, '/', function)
| project timestamp, skillFunction, success, userId, environment
| order by timestamp desc
| limit 100
```

Or to report the success rate of skill functions against environments, you can first add a parameter to the dashboard to filter the environment.

You can use this query to show the environments available by adding the `Source` as this `Query`:

```kql
customEvents
| where timestamp between (['_startTime'] .. ['_endTime']) // Time range filtering
| extend environment = tostring(customDimensions.AspNetCoreEnvironment)
| distinct environment
```

Name the variable `_environment`, select `Multiple Selection` and tick `Add empty "Select all" value`. Finally `Select all` as the `Default value`.

You can then query the success rate with this query:

```kql
customEvents
| where timestamp between (_startTime .. _endTime)
| where name == "SkillFunction"
| extend skill = tostring(customDimensions.skillName)
| extend function = tostring(customDimensions.functionName)
| extend success = tobool(customDimensions.success)
| extend environment = tostring(customDimensions.AspNetCoreEnvironment)
| extend skillFunction = strcat(skill, '/', function)
| summarize Total=count(), Success=countif(success) by skillFunction, environment
| project skillFunction, SuccessPercentage = 100.0 * Success/Total, environment
| order by SuccessPercentage asc
```

You may wish to use the Visual tab to turn on conditional formatting to highlight low success rates or render it as a chart.

Finally you could render this data over time with a query like this:

```kql
customEvents
| where timestamp between (_startTime .. _endTime)
| where name == "SkillFunction"
| extend skill = tostring(customDimensions.skillName)
| extend function = tostring(customDimensions.functionName)
| extend success = tobool(customDimensions.success)
| extend environment = tostring(customDimensions.AspNetCoreEnvironment)
| extend skillFunction = strcat(skill, '/', function)
| summarize Total=count(), Success=countif(success) by skillFunction, environment, bin(timestamp,1m)
| project skillFunction, SuccessPercentage = 100.0 * Success/Total, environment, timestamp
| order by timestamp asc
```

Then use a Time chart on the Visual tab.