---
status: { accepted }
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
- The following metrics should be emitted by SK:
  - Input token usage for prompt (Prompt)
    - Description: A prompt is the smallest unit that consumes tokens (`KernelFunctionFromPrompt`).
    - Dimensions: ComponentType, ComponentName, Service ID, Model ID
    - Type: Histogram
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
    - Type: Histogram
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
    - Type: Histogram
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
    - Type: Counter
    - Example:
      | ComponentType | ComponentName | Fail | Success
      |---|---|---|---|
      | Planner | CreateHandlebarsPlan | 5 | 95
      | Planner | CreateHSequentialPlan | 20 | 80
  - Success/failure count for plans
    - Description: A plan execution is considered successful when all steps in the plan are executed successfully.
    - Dimensions: ComponentType, ComponentName, Service ID, Model ID
    - Type: Counter
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

- Bottom-up: Propagate token usage information from connectors back to the functions.
- Top-down: Propagate function information down to the connectors, enabling them to tag metric items with function information.

We have decided to implement the bottom-up approach for the following reasons:

1. SK is already configured to propagate token usage information from connectors via `ContentBase`. We simply need to extend the list of items that need to be propagated, such as model information.
2. Currently, SK does not have a method for passing function information down to the connector level. Although we considered using [baggage](https://opentelemetry.io/docs/concepts/signals/baggage/#:~:text=In%20OpenTelemetry%2C%20Baggage%20is%20contextual%20information%20that%E2%80%99s%20passed,available%20to%20any%20span%20created%20within%20that%20trace.) as a means of propagating information downward, experts from the OpenTelemetry team advised against this approach due to security concerns.

With the bottom-up approach, we need to retrieve the token usage information from the metadata:

```csharp
// Note that not all services support usage details.
/// <summary>
/// Captures usage details, including token information.
/// </summary>
private void CaptureUsageDetails(string? modelId, IDictionary<string, object?>? metadata, ILogger logger)
{
  if (string.IsNullOrWhiteSpace(modelId))
  {
    logger.LogWarning("No model ID provided to capture usage details.");
    return;
  }

  if (metadata is null)
  {
    logger.LogWarning("No metadata provided to capture usage details.");
    return;
  }

  if (!metadata.TryGetValue("Usage", out object? usageObject) || usageObject is null)
  {
    logger.LogWarning("No usage details provided to capture usage details.");
    return;
  }

  var promptTokens = 0;
  var completionTokens = 0;
  try
  {
    var jsonObject = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize(usageObject));
    promptTokens = jsonObject.GetProperty("PromptTokens").GetInt32();
    completionTokens = jsonObject.GetProperty("CompletionTokens").GetInt32();
  }
  catch (Exception ex) when (ex is KeyNotFoundException)
  {
    logger.LogInformation("Usage details not found in model result.");
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
    { "semantic_kernel.function.name", this.Name },
    { "semantic_kernel.function.model_id", modelId }
  };

  s_invocationTokenUsagePrompt.Record(promptTokens, in tags);
  s_invocationTokenUsageCompletion.Record(completionTokens, in tags);
}
```

> Note that we do not consider services that do not return token usage. Currently only OpenAI & Azure OpenAI services return token usage information.

## Decision Outcome

1. New metrics names:
   | Meter | Metrics |
   |---|---|
   |Microsoft.SemanticKernel.Planning| <ul><li>semantic_kernel.planning.invoke_plan.duration</li></ul> |
   |Microsoft.SemanticKernel| <ul><li>semantic_kernel.function.invocation.token_usage.prompt</li><li>semantic_kernel.function.invocation.token_usage.completion</li></ul> |
   > Note: we are also replacing the "sk" prefixes with "semantic_kernel" for all existing metrics to avoid ambiguity.
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
// Use LoggerMessage attribute for optimal performance
this._logger.LogPlanCreationStarted();
this._logger.LogPlanCreated();
```

#### [Metrics](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/metrics)

Metrics will be used to record measurements overtime.

```csharp
/// <summary><see cref="Meter"/> for function-related metrics.</summary>
private static readonly Meter s_meter = new("Microsoft.SemanticKernel");

/// <summary><see cref="Histogram{T}"/> to record plan execution duration.</summary>
private static readonly Histogram<double> s_planExecutionDuration =
  s_meter.CreateHistogram<double>(
    name: "semantic_kernel.planning.invoke_plan.duration",
    unit: "s",
    description: "Duration time of plan execution.");

TagList tags = new() { { "semantic_kernel.plan.name", planName } };

try
{
  ...
}
catch (Exception ex)
{
  // If a measurement is tagged with "error.type", then it's a failure.
  tags.Add("error.type", ex.GetType().FullName);
}

s_planExecutionDuration.Record(duration.TotalSeconds, in tags);
```

#### [Traces](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/distributed-tracing)

Activities are used to track dependencies through an application, correlating work done by other components, and form a tree of activities known as a trace.

```csharp
ActivitySource s_activitySource = new("Microsoft.SemanticKernel");

// Create and start an activity
using var activity = s_activitySource.StartActivity(this.Name);

// Use LoggerMessage attribute for optimal performance
logger.LoggerGoal(goal);
logger.LoggerPlan(plan);
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
