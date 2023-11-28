---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-11-28
deciders: matthewbolanos,markwallace-microsoft,alliscode
consulted:
informed:
---

# Planners as Plugins

## Context and Problem Statement

### Context

Historically, planners have consisted of two parts:

1. A planner object that uses a prompt (or series of prompts) to generate a plan object with the available functions in the kernel.
2. A plan object that contains an instruction set that can be invoked by the kernel. This instruction set uses the functions available in the kernel and is serializable / deserializable.

```csharp
// The planner object
var planner = new HandlebarsPlanner(
    kernel,
    new HandlebarsPlannerConfig()
    {
        AllowLoops = allowLoopsInPlan
    });

// The plan object
var plan = await planner.CreatePlanAsync(goal);

// Invoking the plan
var result = plan.Invoke(new ContextVariables(), new Dictionary<string, object?>(), CancellationToken.None);
Console.WriteLine($"\nResult:\n{result.GetValue<string>()}\n");
```

Not all planners follow this pattern though. For example, the `FunctionCallingStepwisePlanner` does not have a plan object. Instead, you simply execute the planner once and internally it iteratively invokes the functions necessary to complete the user's goal.

```csharp
// The planner object
var planner = new FunctionCallingStepwisePlanner(kernel, config);

FunctionCallingStepwisePlannerResult result = await planner.ExecuteAsync(question);
Console.WriteLine($"Answer: {result.FinalAnswer}");
```

### Problem Statement

There are a few problems with the current planner pattern:

1. A planner object can only be bound to a single kernel during construction time.
2. If a developer wants to use the output of a planner and its plan in a template (common for Copilot experiences), they must wrap the planner in a `KernelFunction`.
3. Under-the-hood, each planner leverages AI services to generate a plan, but this is a black box to the developer. They cannot alter which AI service is used or its execution settings.
4. The current planners do not leverage the hooks system on the kernel.
5. Developers need to write additional code to invoke a plan object.

The goal of this ADR is to address these problems by modeling planners as plugins.

## Decision Drivers

1. The Semantic Kernel developer should be able to set the model and execution settings with the `AISelectorService`.

2. The Semantic Kernel developer should be able to easily use the results of a planner in a prompt template.

3. The Semantic Kernel developer should be able to use the hooks system on the kernel to perform Responsible AI, telemetry, and saving of plans.

## Out of Scope

- The previous planners (i.e., Action Planner, Sequential Planner, and V1 of Stepwise planner)

## Considered Options

### Option 1 - Dedicated Streaming Interfaces

By extending the `IKernelPlugin` interface, planners can become plugins that can be loaded into the kernel. This allows users to easily call the planner from a template (or even allow the planner to be called from other planners if desired). The planner will have a single main function that will generate a plan and execute it.

## User Experience Goal

```csharp
// Create a new instance of the handlebars planner with the plugin name "MathSolver"
var plannerPlugin = new HandlebarsPlannerPlugin("MathSolver");

// Hooks can be added to the plugin to perform Responsible AI, telemetry, and saving of plans
kernel.FunctionInvoked += InspectAndSavePlanHandler;

// Add the plugin to the kernel
kernel.AddPlugin(plannerPlugin);

// Call the planner and get the result
// In the `ExecuteAsync` method, the planner will generate a plan and execute it
var result = await kernel.RunAsync(plannerPlugin["Execute"], new() {{ "goal", "What is 2+2?" }});
```

Within a prompt template, they could also call the planner like so:

```handlebars
<message role="user">
  {{math_question}}
</message>
<message role="system">
  {{MathSolver_Execute goal=math_question}}
</message>
```

## Implementing planner plugins

In option 1, the planners are implemented as an extension to the `IKernelPlugin` interface. To implement the `IKernelPlugin` interface, the planner must implement `Name`, `Description`, `this[string functionName]`, and `TryGetFunction(string functionName, out KernelFunction? function)`. To do so, the following steps should be taken:

- Create a new class that implements `IKernelPlugin`
- In the constructor, provide overrides for `Name` and `Description` (otherwise they will default to the class name and an empty string)
- Create an `ExecuteAsync` method that can be expressed as a `KernelFunction`
  - In the `ExecuteAsync` method, the planner should create a new plan and execute it
  - The prompt that creates the plan should be a `KernelFunction` named `CreatePlan` so that hooks can be added to it and so the execution settings can be set
  - In the case of the `HandlebarsPlanner`, the plan should be another `KernelFunction` named `RunPlan` so that hooks can be added to it
  - In the case of the `FunctionCallingStepwisePlanner`, the prompt that gets the function call should be a `KernelFunction` named `GetFunction` so that hooks can be added to it
  - The `CreatePlan`, `GetFunction`, and `RunPlan` functions can be invoked by the kernel with `Kernel.RunAsync(runPlanFunction, variables, cancellationToken)`, they should not be registered with the kernel to avoid mutating the kernel state
- Implement `this[string functionName]` and `TryGetFunction(string functionName, out KernelFunction? function)` to return the `KernelFunction` created in `ExecuteAsync`

## Pros

1. All parts of planners can have hooks added to them
2. Planners can be reused by multiple kernels
3. Planners can be called from templates

## Cons

1. Planners must be implemented as `IKernelPlugin`s

### Option 2 - Dedicated Streaming Interfaces (Returning a Class)

Instead of implementing the `IKernelPlugin` interface, we could simply load the class using the `ImportPluginFromObject` method.

## User Experience Goal

```csharp
// Create a new instance of the handlebars planner with the plugin name "MathSolver"
var plannerPlugin = kernel.ImportPluginFromObject<HandlebarsPlanner>("MathSolver");

// Hooks can be added to the plugin to perform Responsible AI, telemetry, and saving of plans
kernel.FunctionInvoked += InspectAndSavePlanHandler;

// Call the planner and get the result
// In the `ExecuteAsync` method, the planner will generate a plan and execute it
var result = await kernel.RunAsync(plannerPlugin["Execute"], new() {{ "goal", "What is 2+2?" }});
```

Within a prompt template, they could also call the planner like so:

```handlebars
<message role="user">
  {{math_question}}
</message>
<message role="system">
  {{MathSolver_Execute goal=math_question}}
</message>
```

## Implementing planner plugins

Unlike option 1, the planners are not implemented as an extension to the `IKernelPlugin` interface. Instead, the planner is simply imported using the `ImportPluginFromObject` method. To do so, the following steps should be taken:

- Create a new class for the planner
- Decorate the `ExecuteAsync` method with the `KernelFunction` attribute
  - In the `ExecuteAsync` method, the planner should create a new plan and execute it
  - The prompt that creates the plan should be a `KernelFunction` named `CreatePlan` so that hooks can be added to it and so the execution settings can be set
  - In the case of the `HandlebarsPlanner`, the plan should be another `KernelFunction` named `RunPlan` so that hooks can be added to it
  - In the case of the `FunctionCallingStepwisePlanner`, the prompt that gets the function call should be a `KernelFunction` named `GetFunction` so that hooks can be added to it
  - The `CreatePlan`, `GetFunction`, and `RunPlan` functions can be invoked by the kernel with `Kernel.RunAsync(runPlanFunction, variables, cancellationToken)`, they should not be registered with the kernel to avoid mutating the kernel state
- Do _not_ add any methods other than `ExecuteAsync` to the class with the `KernelFunction` attribute

## Pros

1. All benefits from Option 1 +
2. Doesn't require the planner to implement the `IKernelPlugin` interface (which is a bit odd)
3. The name and description of the plugin is automatically handled by the `ImportPluginFromObject` method
4. Slightly fewer lines of code to implement for the developer

## Cons

1. All of the sub-functions of the planner must be implemented without using the `KernelFunction` attribute.

## Decision Outcome
