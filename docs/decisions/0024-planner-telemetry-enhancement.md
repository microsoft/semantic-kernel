---
status: { proposed }
contact: { TaoChenOSU }
date: { 2023-11-21 }
deciders: alliscode, dmytrostruk, markwallace, SergeyMenshykh, stephentoub
consulted: {}
informed: {}
---

# Planner Telemetry Enhancement

## Context and Problem Statement

It would be extremely beneficial for applications using Semantic Kernel's planning features to be able to continuously monitor the performance of planners and plans as well as debugging them.

## Scenarios

Contoso is a company that is developing an AI application using SK.

1. Contoso needs to continuously monitor the token usage of a particular planner, including prompt tokens, completion tokens, and the total tokens.
2. Contoso needs to continuously monitor the time it takes for a particular planner to create a plan.
3. Contoso needs to continuously monitor the success rate of a particular planner in creating a valid plan.
4. Contoso needs to continuously monitor the success rate of a particular plan type being executed successfully.
5. Contoso wants to be able to see the token usage of a particular planner run.
6. Contoso wants to be able to see the time taken to create a plan of a particular planner run.
7. Contoso wants to be able to see the steps in a plan.
8. Contoso wants to be able to see the inputs&outputs of each plan step.
9. Contoso wants to change a few settings that may affect the performance of the planners. They would like to know how the performance will be affected before committing the changes.
10. Contoso wants to update to a new model that is cheaper and faster. They would like to know how the new model performs in planning tasks.

## Out of scope

1. We provide an example on how to send telemetry to Application Insights. Although other telemetry service options are supported technically, we will not cover possible ways of setting them up in this ADR.
2. This ADR does not seek to modify the current instrumentation design in SK.
3. We do not consider services that do not return token usage.

## Decision Drivers

- The framework should be telemetry service agnostic.
- Enabling and disabling specific telemetry items should require minimum effort, given an item can be turned on and off.

- The following metrics should be emitted by SK:
  - Input token usage for prompt (Prompt)
    - Description: A prompt is the smallest unit that consumes tokens (`KernelFunctionFromPrompt`).
    - Dimensions: ComponentType, ComponentName, Service ID, Model ID
    - Example:
      | ComponentType | ComponentName | Service ID | Model ID | Value |
      |---|---|---|---|---|
      | Function | WritePoem | | GPT-3.5-Turbo | 40
      | Function | TellJoke | | GPT-4 | 50
      | Function | WriteAndTellJoke | | GPT-3.5-Turbo | 30
      | Planner | CreateHandlebarsPlan | | GPT-3.5-Turbo | 100
  - Output token usage for prompt (Completion)
    - Description: A prompt is the smallest unit that consumes tokens (`KernelFunctionFromPrompt`).
    - Dimensions: ComponentType, ComponentName, Service ID, Model ID
    - Example:
      | ComponentType | ComponentName | Service ID | Model ID | Value |
      |---|---|---|---|---|
      | Function | WritePoem | | GPT-3.5-Turbo | 40
      | Function | TellJoke | | GPT-4 | 50
      | Function | WriteAndTellJoke | | GPT-3.5-Turbo | 30
      | Planner | CreateHandlebarsPlan | | GPT-3.5-Turbo | 100
  - Aggregated execution time for functions
    - Description: A function can consist of zero or more prompts. The execution time of a function is the duration from start to end of a function's `invoke` call.
    - Dimensions: ComponentType, ComponentName, Service ID, Model ID
    - Example:
      | ComponentType | ComponentName | Value |
      |---|---|---|
      | Function | WritePoem | 1m
      | Function | TellJoke | 1m
      | Function | WriteAndTellJoke | 1.5m
      | Planner | CreateHandlebarsPlan | 2m
  - Success/failure count for planners
    - Description: A planner run is considered successful when it generates a valid plan. A plan is valid when the model response is successfully parsed into a plan of desired format and it contains one or more steps.
    - Dimensions: ComponentType, ComponentName, Service ID, Model ID
    - Example:
      | ComponentType | ComponentName | Fail | Success
      |---|---|---|---|
      | Planner | CreateHandlebarsPlan | 5 | 95
      | Planner | CreateHSequentialPlan | 20 | 80
  - Success/failure count for plans
    - Description: A plan execution is considered successful when all steps in the plan are executed successfully.
    - Dimensions: ComponentType, ComponentName, Service ID, Model ID
    - Example:
      | ComponentType | ComponentName | Fail | Success
      |---|---|---|---|
      | Plan | HandlebarsPlan | 5 | 95
      | Plan | SequentialPlan | 20 | 80

## Considered Options

- Function hooks
  - Inject logic to functions that will get executed before or after a function is invoked.
- Instrumentation
  - Logging
  - Metrics
  - Traces

## Other Considerations

SK currently tracks token usage metrics in connectors; however, these metrics are not categorized. Consequently, developers cannot determine token usage for different operations. To address this issue, we propose the following two approaches:

- Bottom-up: Propagate token usage information from connectors back to the functions, along with model results (See [Option 1](#option-1) and [Option 2](#option-2) under this section).
- Top-down: Propagate function information down to the connectors, enabling them to tag metric items with function information.

We have decided to implement the bottom-up approach for the following reasons:

1. SK is already configured to propagate token usage information from connectors via `ModelResult`. We simply need to extend the list of items that get propagated, such as model information.
2. Currently, SK does not have a method for passing function information down to the connector level. Although we considered using [baggage](https://opentelemetry.io/docs/concepts/signals/baggage/#:~:text=In%20OpenTelemetry%2C%20Baggage%20is%20contextual%20information%20that%E2%80%99s%20passed,available%20to%20any%20span%20created%20within%20that%20trace.) as a means of propagating information downward, experts from the OpenTelemetry team advised against this approach due to security concerns.

With the bottom-up approach, we need to propagate model information from connectors to functions.

#### Option 1

Add to `IResultBase`:

```csharp
/// <summary>
/// Interface for model results
/// </summary>
public interface IResultBase
{
  /// <summary>
  /// Model name or Id
  /// </summary>
  string ModelId { get; }

  /// <summary>
  /// Gets the model result data.
  /// </summary>
  ModelResult ModelResult { get; }
}
```

#### Option 2

Add to `ModelResult`:

```csharp
public sealed class ModelResult
{
    private readonly object _result;

    public ModelResult(object result, string modelId)
    {
        Verify.NotNull(result);

        this._result = result;
        this.ModelId = modelId;
    }

    public string ModelId { get; }

    ...
}
```

We also need to propagate the model Id up via KernelResult:

```csharp
// In AIFunctionResultExtensions.cs
...
/// <summary>
/// Function model id key for <see cref="ModelResult"/> records.
/// </summary>
public const string ModelIdKey = "ModelId";
...
/// <summary>
/// Returns the model Id from <see cref="FunctionResult"/> metadata.
/// </summary>
/// <param name="result">Instance of <see cref="FunctionResult"/> class.</param>
public static string? GetModelId(this FunctionResult result)
{
  if (result.TryGetMetadataValue(ModelIdKey, out string? modelId))
  {
    return modelId;
  }

  return null;
}


// In KernelFunctionFromPrompt.cs
...
result.Metadata.Add(AIFunctionResultExtensions.ModelIdKey, completionResults[0].ModelId);
...
return result;
```

A kernel function will then retrieve the information by doing the following:

```csharp
// Note that not all services support usage details.
if (result.GetModelId() is null)
{
  logger.LogInformation("Model id not found in function result.");
  return;
}
var modelId = result.GetModelId();

if (result.GetModelResults() is null)
{
  logger.LogInformation("Model results not found in function result.");
  return;
}
var modelResult = result.GetModelResults().FirstOrDefault();
var modelResultJson = modelResult?.GetJsonResult();

var promptTokens = 0;
var completionTokens = 0;
try
{
  var tokenUsage = modelResultJson.GetValueOrDefault().GetProperty("Usage");
  promptTokens = tokenUsage.GetProperty("PromptTokens").GetInt32();
  completionTokens = tokenUsage.GetProperty("CompletionTokens").GetInt32();
}
catch (Exception ex) when (ex is KeyNotFoundException)
{
  logger.LogInformation("Usage details not found in model result.");
  return;
}
catch (Exception ex)
{
  logger.LogError(ex, "Error while parsing usage details from model result.");
  throw;
}


logger.LogInformation(
  "Prompt tokens: {PromptTokens}. Completion tokens: {CompletionTokens}.",
  promptTokens, completionTokens);

TagList tags = new() {
  { "sk.function.name", this.Name },
  { "sk.function.model_id", modelId }
};

// The metrics will be created as private static class members.
s_promptTokensCounter.Add(promptTokens, in tags);
s_completionTokenCounter.Add(completionTokens, in tags);
```

> Note that we do not consider services that do not return token usage. Currently only OpenAI & Azure OpenAI services return token usage information.

## Decision Outcome

1. New metrics names:
   | Meter | Metrics |
   |---|---|
   |Microsoft.SemanticKernel.Planning| <ul><li>sk.planning.create_plan.success</li><li>sk.planning.create_plan.failure</li></ul> |
   |Microsoft.SemanticKernel| <ul><li>sk.function.execution.duration</li><li>sk.function.execution.token_usage.prompt</li><li>sk.function.execution.token_usage.completion</li></ul> |
2. Instrumentation

## Validation

Tests can be added to make sure that all the expected telemetry items are in place and of the correct format.

## Description the Options

### Function hooks

Function hooks allow developers to inject logic to the kernel that will be executed before or after a function is invoked. Example use cases include logging the function input before a function is invoked, and logging results after the function returns.
For more information, please refer to the following ADRs:

1. [Kernel Hooks Phase 1](./0005-kernel-hooks-phase1.md)
2. [Kernel Hooks Phase 2](./0018-kernel-hooks-phase2.md)

We can inject, during function registration, default callbacks to log critical information for all functions.

Pros:

1. Maximum exposure and flexibility to the developers. i.e. App developers can very easily log additional information for individual functions by adding more callbacks.

Cons:

1. Does not create metrics and need additional works to aggregate results.
2. Relying only on logs does not provide trace details.
3. Logs are modified more frequently, which could lead an unstable implementation and require extra maintenance.
4. Hooks only have access to limited function data.

> Note: with distributed tracing already implemented in SK, developers can create custom telemetry within the hooks, which will be sent to the telemetry service once configured, as long as the information is available in the hooks. However, telemetry items created inside the hooks will not be correlated to the functions as parent-child relationships, since they are outside the scope of the functions.

### Distributed tracing

Distributed tracing is a diagnostic technique that can localize failures and performance bottlenecks within distributed applications. .Net has native support to add distributed tracing in libraries and .Net libraries are also instrumented to produce distributed tracing information automatically.

For more information, please refer to this document: [.Net distributed tracing](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/)

Overall pros:

1. Native .Net support.
2. Distributed tracing is already implemented in SK. We just need to add more telemetry.
3. Telemetry service agnostic with [OpenTelemetry](https://opentelemetry.io/docs/what-is-opentelemetry/).

Overall cons:

1. Less flexibility for app developers consuming SK as a library to add custom traces and metrics.

#### Logging

Logs will be used to record interesting events while the code is running.

```csharp
this._logger.LogInformation("{PlannerType}: Received planning request.", PlannerType);
this._logger.LogInformation("{PlannerType}: Successfully created plan. Plan: {plan}", PlannerType, plan.ToPlanString());
```

#### [Metrics](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/metrics)

Metrics will be used to record measurements overtime.

```csharp
/// <summary><see cref="Meter"/> for function-related metrics.</summary>
private static readonly Meter s_meter = new("Microsoft.SemanticKernel");

/// <summary><see cref="Counter{T}"/> to keep track of the number of successful execution.</summary>
private static readonly Counter<int> s_successCounter = s_meter.CreateCounter<int>(
    name: "sk.function.success",
    unit: "{execution}",
    description: "Number of successful function executions");

// Add a measurement with a custom dimension to categorize measurements based on function.
s_successCounter.Add(1, new KeyValuePair<string, object>("sk.function.name", this.Name));
```

#### [Traces](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/distributed-tracing)

Activities are used to track dependencies through an application, correlating work done by other components, and form a tree of activities known as a trace.

```csharp
ActivitySource s_activitySource = new("Microsoft.SemanticKernel");

// Create and start an activity
using var activity = s_activitySource.StartActivity(this.Name);

if (logger.IsEnabled(LogLevel.Trace))
{
  logger.LogTrace("Goal: {Goal}", goal); // Sensitive data, logging as trace, disabled by default
}

...

if (logger.IsEnabled(LogLevel.Trace))
{
  logger.LogTrace("Plan: {Plan}", plan); // Sensitive data, logging as trace, disabled by default
}
```

> Note: Trace log will contain sensitive data and should be turned off in production: https://learn.microsoft.com/en-us/dotnet/core/extensions/logging?tabs=command-line#log-level

## Example of how an application would send the telemetry to Application Insights

```csharp
using var traceProvider = Sdk.CreateTracerProviderBuilder()
  .AddSource("Microsoft.SemanticKernel*")
  .AddAzureMonitorTraceExporter(options => options.ConnectionString = connectionString)
  .Build();

using var meterProvider = Sdk.CreateMeterProviderBuilder()
  .AddMeter("Microsoft.SemanticKernel*")
  .AddAzureMonitorMetricExporter(options => options.ConnectionString = connectionString)
  .Build();

using var loggerFactory = LoggerFactory.Create(builder =>
{
  // Add OpenTelemetry as a logging provider
  builder.AddOpenTelemetry(options =>
  {
    options.AddAzureMonitorLogExporter(options => options.ConnectionString = connectionString);
    // Format log messages. This is default to false.
    options.IncludeFormattedMessage = true;
  });
  builder.SetMinimumLevel(MinLogLevel);
});
```

## More information

Additional works that need to be done:

1. Update [telemetry doc](../../dotnet/docs/TELEMETRY.md)
