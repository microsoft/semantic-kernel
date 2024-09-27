# Telemetry

Telemetry in Semantic Kernel (SK) .NET implementation includes _logging_, _metering_ and _tracing_.
The code is instrumented using native .NET instrumentation tools, which means that it's possible to use different monitoring platforms (e.g. Application Insights, Prometheus, Grafana etc.).

Code example using Application Insights can be found [here](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/TelemetryExample).

## Logging

The logging mechanism in this project relies on the `ILogger` interface from the `Microsoft.Extensions.Logging` namespace. Recent updates have introduced enhancements to the logger creation process. Instead of directly using the `ILogger` interface, instances of `ILogger` are now recommended to be created through an `ILoggerFactory` provided to components using the `WithLoggerFactory` method.

By employing the `WithLoggerFactory` approach, logger instances are generated with precise type information, facilitating more accurate logging and streamlined control over log filtering across various classes.

Log levels used in SK:

- Trace - this type of logs **should not be enabled in production environments**, since it may contain sensitive data. It can be useful in test environments for better observability. Logged information includes:
  - Goal/Ask to create a plan
  - Prompt (template and rendered version) for AI to create a plan
  - Created plan with function arguments (arguments may contain sensitive data)
  - Prompt (template and rendered version) for AI to execute a function
  - Arguments to functions (arguments may contain sensitive data)
- Debug - contains more detailed messages without sensitive data. Can be enabled in production environments.
- Information (default) - log level that is enabled by default and provides information about general flow of the application. Contains following data:
  - AI model used to create a plan
  - Plan creation status (Success/Failed)
  - Plan creation execution time (in seconds)
  - Created plan without function arguments
  - AI model used to execute a function
  - Function execution status (Success/Failed)
  - Function execution time (in seconds)
- Warning - includes information about unusual events that don't cause the application to fail.
- Error - used for logging exception details.

### Examples

Enable logging for Kernel instance:

```csharp
var kernel = new KernelBuilder().WithLoggerFactory(loggerFactory);
```

All kernel functions and planners will be instrumented. It includes _logs_, _metering_ and _tracing_.

### Log Filtering Configuration

Log filtering configuration has been refined to strike a balance between visibility and relevance:

```csharp
// Add OpenTelemetry as a logging provider
builder.AddOpenTelemetry(options =>
{
  options.AddAzureMonitorLogExporter(options => options.ConnectionString = connectionString);
  // Format log messages. This is default to false.
  options.IncludeFormattedMessage = true;
});
builder.AddFilter("Microsoft", LogLevel.Warning);
builder.AddFilter("Microsoft.SemanticKernel", LogLevel.Critical);
builder.AddFilter("Microsoft.SemanticKernel.Reliability", LogLevel.Information);
```

> Read more at: https://github.com/open-telemetry/opentelemetry-dotnet/blob/main/docs/logs/customizing-the-sdk/README.md

## Metering

Metering is implemented with `Meter` class from `System.Diagnostics.Metrics` namespace.

Available meters:

- _Microsoft.SemanticKernel.Planning_ - contains all metrics related to planning. List of metrics:
  - `semantic_kernel.planning.create_plan.duration` (Histogram) - execution time of plan creation (in seconds)
  - `semantic_kernel.planning.invoke_plan.duration` (Histogram) - execution time of plan execution (in seconds)
- _Microsoft.SemanticKernel_ - captures metrics for `KernelFunction`. List of metrics:
  - `semantic_kernel.function.invocation.duration` (Histogram) - function execution time (in seconds)
  - `semantic_kernel.function.streaming.duration` (Histogram) - function streaming execution time (in seconds)
  - `semantic_kernel.function.invocation.token_usage.prompt` (Histogram) - number of prompt token usage (only for `KernelFunctionFromPrompt`)
  - `semantic_kernel.function.invocation.token_usage.completion` (Histogram) - number of completion token usage (only for `KernelFunctionFromPrompt`)
- _Microsoft.SemanticKernel.Connectors.OpenAI_ - captures metrics for OpenAI functionality. List of metrics:
  - `semantic_kernel.connectors.openai.tokens.prompt` (Counter) - number of prompt tokens used.
  - `semantic_kernel.connectors.openai.tokens.completion` (Counter) - number of completion tokens used.
  - `semantic_kernel.connectors.openai.tokens.total` (Counter) - total number of tokens used.

Measurements will be associated with tags that will allow data to be categorized for analysis:

```csharp
TagList tags = new() { { "semantic_kernel.function.name", this.Name } };
s_invocationDuration.Record(duration.TotalSeconds, in tags);
```

### [Examples](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/TelemetryExample/Program.cs)

Depending on monitoring tool, there are different ways how to subscribe to available meters. Following example shows how to subscribe to available meters and export metrics to Application Insights using `OpenTelemetry.Sdk`:

```csharp
using var meterProvider = Sdk.CreateMeterProviderBuilder()
  .AddMeter("Microsoft.SemanticKernel*")
  .AddAzureMonitorMetricExporter(options => options.ConnectionString = connectionString)
  .Build();
```

> Read more at: https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=net

> Read more at: https://github.com/open-telemetry/opentelemetry-dotnet/blob/main/docs/metrics/customizing-the-sdk/README.md

## Tracing

Tracing is implemented with `Activity` class from `System.Diagnostics` namespace.

Available activity sources:

- _Microsoft.SemanticKernel.Planning_ - creates activities for all planners.
- _Microsoft.SemanticKernel_ - creates activities for `KernelFunction`.

### Examples

Subscribe to available activity sources using `OpenTelemetry.Sdk`:

```csharp
using var traceProvider = Sdk.CreateTracerProviderBuilder()
  .AddSource("Microsoft.SemanticKernel*")
  .AddAzureMonitorTraceExporter(options => options.ConnectionString = connectionString)
  .Build();
```

> Read more at: https://github.com/open-telemetry/opentelemetry-dotnet/blob/main/docs/trace/customizing-the-sdk/README.md
