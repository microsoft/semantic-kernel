# Semantic Kernel Telemetry Example

This example project shows how an application can be configured to send Semantic Kernel telemetry to Application Insights.

> Note that it is also possible to use other Application Performance Management (APM) vendors. An example is [Prometheus](https://prometheus.io/docs/introduction/overview/). Please refer to this [link](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/metrics-collection#configure-the-example-app-to-use-opentelemetrys-prometheus-exporter) on how to do it.

For more information, please refer to the following articles:

1. [Observability](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/observability-with-otel)
2. [OpenTelemetry](https://opentelemetry.io/docs/)
3. [Enable Azure Monitor OpenTelemetry for .Net](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=net)
4. [Configure Azure Monitor OpenTelemetry for .Net](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-configuration?tabs=net)
5. [Add, modify, and filter Azure Monitor OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-add-modify?tabs=net)
6. [Customizing OpenTelemetry .NET SDK for Metrics](https://github.com/open-telemetry/opentelemetry-dotnet/blob/main/docs/metrics/customizing-the-sdk/README.md)
7. [Customizing OpenTelemetry .NET SDK for Logs](https://github.com/open-telemetry/opentelemetry-dotnet/blob/main/docs/logs/customizing-the-sdk/README.md)

## What to expect

In this example project, the Handlebars planner will be invoked to achieve a goal. The planner will request the model to create a plan, comprising three steps, with two of them being prompt-based kernel functions. The plan will be executed to produce the desired output, effectively fulfilling the goal.

The Semantic Kernel SDK is designed to efficiently generate comprehensive logs, traces, and metrics throughout the planner invocation, as well as during function and plan execution. This allows you to effectively monitor your AI application's performance and accurately track token consumption.

> `ActivitySource.StartActivity` internally determines if there are any listeners recording the Activity. If there are no registered listeners or there are listeners that are not interested, StartActivity() will return null and avoid creating the Activity object. Read more [here](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/distributed-tracing-instrumentation-walkthroughs).

## Configuration

### Require resources

1. [Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource)
2. [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal)

### Secrets

This example will require secrets and credentials to access your Application Insights instance and Azure OpenAI.
We suggest using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

To set your secrets with Secret Manager:

```
cd dotnet/samples/TelemetryExample

dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "..."
dotnet user-secrets set "AzureOpenAI:ChatModelId" "..."
dotnet user-secrets set "AzureOpenAI:Endpoint" "https://... .openai.azure.com/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "..."

dotnet user-secrets set "ApplicationInsights:ConnectionString" "..."
```

## Running the example

Simply run `dotnet run` under this directory if the command line interface is preferred. Otherwise, this example can also be run in Visual Studio.

> This will output the Operation/Trace ID, which can be used later in Application Insights for searching the operation.

## Application Insights/Azure Monitor

### Logs and traces

Go to your Application Insights instance, click on _Transaction search_ on the left menu. Use the operation id output by the program to search for the logs and traces associated with the operation. Click on any of the search result to view the end-to-end transaction details. Read more [here](https://learn.microsoft.com/en-us/azure/azure-monitor/app/transaction-search-and-diagnostics?tabs=transaction-search).

### Metrics

Running the application once will only generate one set of measurements (for each metrics). Run the application a couple times to generate more sets of measurements.

> Note: Make sure not to run the program too frequently. Otherwise, you may get throttled.

Please refer to here on how to analyze metrics in [Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/analyze-metrics).

### Log Analytics

It is also possible to use Log Analytics to query the telemetry items sent by the sample application. Please read more [here](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-tutorial).

For example, to create a pie chart to summarize the Handlebars planner status:

```kql
dependencies
| where name == "Microsoft.SemanticKernel.Planning.Handlebars.HandlebarsPlanner"
| extend status = iff(success == True, "Success", "Failure")
| summarize count() by status
| render piechart
```

Or to create a bar chart to summarize the Handlebars planner status by date:

```kql
dependencies
| where name == "Microsoft.SemanticKernel.Planning.Handlebars.HandlebarsPlanner"
| extend status = iff(success == True, "Success", "Failure"), day = bin(timestamp, 1d)
| project day, status
| summarize
    success = countif(status == "Success"),
    failure = countif(status == "Failure") by day
| extend day = format_datetime(day, "MM/dd/yy")
| order by day
| render barchart
```

Or to see status and performance of each planner run:

```kql
dependencies
| where name == "Microsoft.SemanticKernel.Planning.Handlebars.HandlebarsPlanner"
| extend status = iff(success == True, "Success", "Failure")
| project timestamp, id, status, performance = performanceBucket
| order by timestamp
```

It is also possible to summarize the total token usage:

```kql
customMetrics
| where name == "semantic_kernel.connectors.openai.tokens.total"
| project value
| summarize sum(value)
| project Total = sum_value
```

Or track token usage by functions:

```kql
customMetrics
| where name == "semantic_kernel.function.invocation.token_usage.prompt" and customDimensions has "semantic_kernel.function.name"
| project customDimensions, value
| extend function = tostring(customDimensions["semantic_kernel.function.name"])
| project function, value
| summarize sum(value) by function
| render piechart
```

### Azure Dashboard

You can create an Azure Dashboard to visualize the custom telemetry items. You can read more here: [Create a new dashboard](https://learn.microsoft.com/en-us/azure/azure-monitor/app/overview-dashboard#create-a-new-dashboard).

## More information

- [Telemetry docs](../../docs/TELEMETRY.md)
- [Planner telemetry improvement ADR](../../../docs/decisions/0025-planner-telemetry-enhancement.md)
