# Telemetry

Telemetry in Semantic Kernel (SK) .NET implementation includes _logging_, _metering_ and _tracing_.
The code is instrumented using native .NET instrumentation tools, which means that it's possible to use different monitoring platforms (e.g. Application Insights, Prometheus, Grafana etc.).

Code example using Application Insights can be found [here](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/ApplicationInsightsExample/Program.cs).

## Logging

The logging mechanism in this project relies on the `ILogger` interface from the `Microsoft.Extensions.Logging` namespace. Recent updates have introduced enhancements to the logger creation process. Instead of directly using the `ILogger` interface, instances of `ILogger` are now recommended to be created through an `ILoggerFactory` provided to components using the `WithLoggerFactory` method.

By employing the `WithLoggerFactory` approach, logger instances are generated with precise type information, facilitating more accurate logging and streamlined control over log filtering across various classes.

Log levels used in SK:

- Trace - this type of logs **should not be enabled in production environments**, since it may contain sensitive data. It can be useful in test environments for better observability. Logged information includes:
  - Goal/Ask to create a plan
  - Prompt (template and rendered version) for AI to create a plan
  - Created plan with function arguments (arguments may contain sensitive data)
  - Prompt (template and rendered version) for AI to execute a function
- Debug - contains more detailed messages without sensitive data. Can be enabled in production environments.
- Information (default) - log level that is enabled by default and provides information about general flow of the application. Contains following data:
  - AI model used to create a plan
  - Plan creation status (Success/Failed)
  - Plan creation execution time (in milliseconds)
  - Created plan without function arguments
  - AI model used to execute a function
  - Function execution status (Success/Failed)
  - Function execution time (in milliseconds)
- Warning - includes information about unusual events that don't cause the application to fail.
- Error - used for logging exception details.

### Examples

Enable logging for Kernel instance:

```csharp
var kernel = new KernelBuilder().WithLoggerFactory(loggerFactory);
```

Enable logging for Planner instance (_metering_ and _tracing_ will be enabled as well):

```csharp
var planner = new SequentialPlanner(kernel, plannerConfig).WithInstrumentation(loggerFactory);
```

### Log Filtering Configuration

Log filtering configuration has been refined to strike a balance between visibility and relevance:

```csharp
builder.AddFilter("Microsoft", LogLevel.Warning);
builder.AddFilter("Microsoft.SemanticKernel", LogLevel.Critical);
builder.AddFilter("Microsoft.SemanticKernel.Reliability", LogLevel.Information);
```

## Metering

Metering is implemented with `Meter` class from `System.Diagnostics.Metrics` namespace.

Available meters:

- _Microsoft.SemanticKernel.Planning.Action.InstrumentedActionPlanner_ - captures metrics for `ActionPlanner`. List of metrics:
  - `SK.ActionPlanner.CreatePlan.ExecutionTime` - execution time of plan creation (in milliseconds)
- _Microsoft.SemanticKernel.Planning.Sequential.InstrumentedSequentialPlanner_ - captures metrics for `SequentialPlanner`. List of metrics:
  - `SK.SequentialPlanner.CreatePlan.ExecutionTime` - execution time of plan creation (in milliseconds)
- _Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlanner_ - captures metrics for `StepwisePlanner`. List of metrics:
  - `SK.StepwisePlanner.CreatePlan.ExecutionTime` - execution time of plan creation (in milliseconds)
- _Microsoft.SemanticKernel.Planning.Plan_ - captures metrics for `Plan`. List of metrics:
  - `SK.Plan.Execution.ExecutionTime` - plan execution time (in milliseconds)
  - `SK.Plan.Execution.ExecutionTotal` - total number of plan executions
  - `SK.Plan.Execution.ExecutionSuccess` - number of successful plan executions
  - `SK.Plan.Execution.ExecutionFailure` - number of failed plan executions
- _Microsoft.SemanticKernel.SkillDefinition.SKFunction_ - captures metrics for `SKFunction`. List of metrics:
  - `SK.<SkillName><FunctionName>.ExecutionTime` - function execution time (in milliseconds)
  - `SK.<SkillName><FunctionName>.ExecutionTotal` - total number of function executions
  - `SK.<SkillName><FunctionName>.ExecutionSuccess` - number of successful function executions
  - `SK.<SkillName><FunctionName>.ExecutionFailure` - number of failed function executions
- _Microsoft.SemanticKernel.Connectors.AI.OpenAI_ - captures metrics for OpenAI functionality. List of metrics:
  - `SK.Connectors.OpenAI.PromptTokens` - number of prompt tokens used.
  - `SK.Connectors.OpenAI.CompletionTokens` - number of completion tokens used.
  - `SK.Connectors.OpenAI.TotalTokens` - total number of tokens used.

### Examples

Depending on monitoring tool, there are different ways how to subscribe to available meters. Following example shows how to subscribe to available meters and export metrics to Application Insights using `MeterListener`:

```csharp
var meterListener = new MeterListener();

meterListener.InstrumentPublished = (instrument, listener) =>
{
    if (instrument.Meter.Name.StartsWith("Microsoft.SemanticKernel", StringComparison.Ordinal))
    {
        listener.EnableMeasurementEvents(instrument);
    }
};

// Set callback to specific numeric type - double.
meterListener.SetMeasurementEventCallback<double>((instrument, measurement, tags, state) =>
{
    // Export to Application Insights using telemetry client instance
    telemetryClient.GetMetric(instrument.Name).TrackValue(measurement);
});

meterListener.Start();
```

It's possible to control for what meters to subscribe. For example, following condition will allow to subscribe to all meters in Semantic Kernel:

```csharp
instrument.Meter.Name.StartsWith("Microsoft.SemanticKernel", StringComparison.Ordinal)
```

It's also possible to subscribe to specific meter. Following condition will allow to subscribe to meter for `SKFunction` only:

```csharp
instrument.Meter.Name.Equals("Microsoft.SemanticKernel.SkillDefinition.SKFunction", StringComparison.Ordinal)
```

## Tracing

Tracing is implemented with `Activity` class from `System.Diagnostics` namespace.

Available activity sources:

- _Microsoft.SemanticKernel.Planning.Action.InstrumentedActionPlanner_ - creates activities for `ActionPlanner`.
- _Microsoft.SemanticKernel.Planning.Sequential.InstrumentedSequentialPlanner_ - creates activities for `SequentialPlanner`.
- _Microsoft.SemanticKernel.Planning.Stepwise.StepwisePlanner_ - creates activities for `StepwisePlanner`.
- _Microsoft.SemanticKernel.Planning.Plan_ - creates activities for `Plan`.
- _Microsoft.SemanticKernel.SkillDefinition.SKFunction_ - creates activities for `SKFunction`.

### Examples

Subscribe to available activity sources using `ActivityListener`:

```csharp
var activityListener = new ActivityListener();

activityListener.ShouldListenTo =
    activitySource => activitySource.Name.StartsWith("Microsoft.SemanticKernel", StringComparison.Ordinal);

ActivitySource.AddActivityListener(activityListener);
```

Following condition will allow to subscribe to all activity sources in Semantic Kernel:

```csharp
activitySource.Name.StartsWith("Microsoft.SemanticKernel", StringComparison.Ordinal)
```

It's also possible to subscribe to specific activity source. Following condition will allow to subscribe to activity source for `SKFunction` only:

```csharp
activitySource.Name.Equals("Microsoft.SemanticKernel.SkillDefinition.SKFunction", StringComparison.Ordinal)
```
