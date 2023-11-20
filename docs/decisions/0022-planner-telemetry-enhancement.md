---
status: { proposed }
contact: { TaoChenOSU }
date: { 2023-11-18 }
deciders: alliscode, dmytrostruk, markwallace, SergeyMenshykh, stephentoub
consulted: {}
informed: {}
---

# Planner Telemetry Enhancement

## Context and Problem Statement

It would be extremely beneficial for applications using Semantic Kernel' planning features to be able to continuously monitor the performance of planners and plans.

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

1. We focus on Application Insights. Although other telemetry service options are supported technically, we will not cover possible ways of setting them up in this ADR.

## Decision Drivers

- The framework should be telemetry service agnostic.
- Enabling and disabling specific telemetry items should require minimum effort.

## Considered Options

- Function hooks
  - Inject logic to functions that will get executed before or after a function is invoked.
- Distributed tracing
  - Activity tags & Metrics
    - Use activities to record individual operations.
    - Use tags in activities to record custom information.
    - Use baggage in activities to more easily correlate dependencies.
    - Use metrics to continuously monitor performance.
  - Logging & Metrics
    - Use logging to record custom information for individual operations.
    - Use metrics to continuously monitor performance.
- Return model token usage as a property of function result.

## Decision Outcome

TBD

## Validation

Tests can be added to make sure that all the expected telemetry items are in place and of the correct format.

## Description the Options

### Function hooks

Function hooks allow developers to inject logic to kernel that will be executed before or after a function is invoked. Example use cases include logging the function input before a function is invoked, and logging results after the function returns.
For more information, please refer to the following ADRs:

1. [Kernel Hooks Phase 1](./0005-kernel-hooks-phase1.md)
2. [Kernel Hooks Phase 2](./0018-kernel-hooks-phase2.md)

This approach will automatically inject default callbacks that sends telemetry data to Application Insights to all functions when the feature is turned on.

Pros:

1. Maximum exposure and flexibility to the developers. i.e. App developers can very easily what additional information is needed for individual functions by adding more callbacks.

Cons:

1. Does not use the existing System.Diagnostic framework that has been set up in the kernel. i.e. InstrumentedSKFunction, InstrumentedPlan, and InstrumentedPlanner.
2. Does not provide the full trace detail.
3. Difficult to create a telemetry service agnostic solution.

### Distributed tracing

Distributed tracing is a diagnostic technique that can localize failures and performance bottlenecks within distributed applications. .Net has native support to add distributed tracing in your libraries and .Net libraries are also instrumented to produce distributed tracing information automatically.

For more information, please refer to this document: [.Net distributed tracing](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/)

Overall pros:

1. Native .Net support and the kernel has set this up.

Overall cons:

1. Less flexibility for app developers to add custom traces and metrics.

#### Metrics

Pros:

1. Easy to use for continuous monitoring.
2. Has been set up in SK.

Cons: No additional cons identified given the scope of this document.

#### Activity tags & baggage

```csharp
// In the instrumented planner
activity?.AddBaggage("Operation", $"{PlannerType}.CreatePlan");

try
{
  ...
  // If planner runs successfully
  activity?.AddTag("Status", "Success");

  // If it's in debugging mode
  // Due to privacy concerns, we need to make certain telemetry items optional.
  activity?.AddTag("Goal", goal);
  activity?.AddTag("Plan", plan.ToSafePlanString());
  activity?.AddTag("ExecutionTime", duration);
}
catch(...)
{
  // If planner fails
  activity?.AddTag("Status", "Failed");
}
```

```csharp
// In Connectors.AI.OpenAI ClientBase.cs
private static readonly ActivitySource s_activitySource = new(typeof(ClientBase).FullName);

// In internal GetTextResults and GetChatResults calls
using var activity = s_activitySource.StartActivity($"{this.GetType().Name}.GetTextResults");
if (activity?.GetBaggageItem("Operation") is not null)
{
    activity?.AddTag("Operation", activity.GetBaggageItem("Operation"));
}
```

In an application that uses SK and Application Insights:

```csharp
var operations = new ConcurrentDictionary<string, IOperationHolder<DependencyTelemetry>>();

// For more detailed tracing we need to attach Activity entity to Application Insights operation manually.
void activityStarted(Activity activity)
{
  var operation = telemetryClient.StartOperation<DependencyTelemetry>(activity);
  operation.Telemetry.Type = activity.Kind.ToString();

  operations.TryAdd(activity.SpanId.ToString(), operation);
}

// We also need to manually stop Application Insights operation when Activity entity is stopped.
void activityStopped(Activity activity)
{
  if (operations.TryRemove(activity.SpanId.ToString(), out var operation))
  {
    activity.Tags.ToList().ForEach(tag =>
    {
      // Add the tags to Application Insights telemetry operations as properties.
      operation.Telemetry.Properties.Add(tag.Key, tag.Value);
    });
    telemetryClient.StopOperation(operation);
  }
}

// Subscribe to all traces in Semantic Kernel
activityListener.ShouldListenTo =
  activitySource => activitySource.Name.StartsWith("Microsoft.SemanticKernel", StringComparison.Ordinal);

activityListener.Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData;
activityListener.SampleUsingParentId = (ref ActivityCreationOptions<string> _) => ActivitySamplingResult.AllData;
activityListener.ActivityStarted = activityStarted;
activityListener.ActivityStopped = activityStopped;

ActivitySource.AddActivityListener(activityListener);
```

The above produces dependency information similar to the screenshot below:

<img src="./images/0022-dependency-in-application-insights-create-plan.png" alt="Example create plan dependency generated in Application Insights" width="400"/>

<img src="./images/0022-dependency-in-application-insights-client-base.png" alt="Example model calling dependency generated in Application Insights" width="400"/>

Cons:

1. Easy to add custom data.
2. Semi-structured data organized by tags (later saved as custom dimensions for Application Insights).
3. Automatically correlated from parent to chid items. Baggage makes it even easier for querying.

Pros:

1. Everything has to a string.
2. Developers may have to creation a new container for each activity depending on the service used.

#### Log

```csharp
this._logger.LogTrace("{PlannerType}: Created plan with details: \n {Plan}", PlannerType, plan.ToPlanString());
```

The above produces trace information similar to the screenshot below:

<img src="./images/0022-trace-in-application-insights.png" alt="Example trace generated in Application Insights" width="400"/>

Cons:

1. More contexture information.
2. Custom data is automatically organized in custom dimensions in Application Insights.

Pros:

1. Logs are modified more frequently.
2. Log configuration will affect what telemetry the libraries produce.
3. More difficult to correlate telemetry items when in query time.
