---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: markwallace
date: 2024-03-15
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk
consulted: 
informed: stoub, matthewbolanos
---

# {short title of solved problem and solution}

## Context and Problem Statement

The `KernelFunctionMetadata.PluginName` property is populated as a side-effect of calling `KernelPlugin.GetFunctionsMetadata`.
The reason for this behavior is to allow a `KernelFunction` instance to be associated with multiple `KernelPlugin` instances.
The downside of this behavior is the `KernelFunctionMetadata.PluginName` property is not available to `IFunctionFilter` callbacks.

The purpose of this ADR is to propose a change that will allow developers to decide when `KernelFunctionMetadata.PluginName` will be populated.

Issues:

1. [Investigate if we should fix the PluginName in the KernelFunction metadata](https://github.com/microsoft/semantic-kernel/issues/4706)
1. [Plugin name inside FunctionInvokingContext in th IFunctionFilter is null](https://github.com/microsoft/semantic-kernel/issues/5452)

## Decision Drivers

- Do not break existing applications.
- Provide ability to make the `KernelFunctionMetadata.PluginName` property available to `IFunctionFilter` callbacks.

## Considered Options

- Clone each `KernelFunction` when it is added to a `KernelPlugin` and set the plugin name in the clone `KernelFunctionMetadata`.
- Add a new parameter to `KernelPluginFactory.CreateFromFunctions` to enable setting the plugin name in the associated `KernelFunctionMetadata` instances. Once set the `KernelFunctionMetadata.PluginName` cannot be changed. Attempting to do so will result in an `InvalidOperationException` being thrown.
- Leave as is and do not support this use case as it may make the behavior of the Semantic Kernel seem inconsistent.

## Decision Outcome

Chosen option: Clone each `KernelFunction`, because result is a consistent behavior and allows the same function can be added to multiple `KernelPlugin`'s.

## Pros and Cons of the Options

### Clone each `KernelFunction`

PR: https://github.com/microsoft/semantic-kernel/pull/5422

- Bad, the same function can be added to multiple `KernelPlugin`'s.
- Bad, because behavior is consistent.
- Good, because there are not breaking change to API signature.
- Bad, because additional `KernelFunction` instances are created.

### Add a new parameter to `KernelPluginFactory.CreateFromFunctions`

PR: https://github.com/microsoft/semantic-kernel/pull/5171

- Good, because no additional `KernelFunction` instances are created.
- Bad, because the same function cannot be added to multiple `KernelPlugin`'s
- Bad, because it will be confusing i.e. depending on how the `KernelPlugin` is created it will behave differently.
- Bad, because there is a minor breaking change to API signature.
