---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: markwallace
date: 2024-02-26
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk
consulted: 
informed: 
---

# Enable setting the plugin name property for a KernelFunction instance

## Context and Problem Statement

The `KernelFunctionMetadata.PluginName` property is populated as a side-effect of calling `KernelPlugin.GetFunctionsMetadata`.
The reason for this behavior is to allow a `KernelFunction` instance to be associated with multiple `KernelPlugin` instances.
The downside of this behavior is the `KernelFunctionMetadata.PluginName` property is not available to `IFunctionFilter` callbacks.

The purpose of this ADR is to propose a change that will allow developers to decide when `KernelFunctionMetadata.PluginName` will be populated.

## Decision Drivers

- Do not break existing applications.
- Provide ability to make the `KernelFunctionMetadata.PluginName` property available to `IFunctionFilter` callbacks.

## Considered Options

- Add a new parameter to `KernelPluginFactory.CreateFromFunctions` to enable setting the plugin name in the associated `KernelFunctionMetadata` instances. Once set the `KernelFunctionMetadata.PluginName` cannot be changed. Attempting to do so will result in an `InvalidOperationException` being thrown.
- Leave as is and do not support this use case as it may make the behavior of the Semantic Kernel seem inconsistent.

## Decision Outcome

Chosen option: "Add a new parameter to `KernelPluginFactory.CreateFromFunctions` to enable setting the plugin name", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.
