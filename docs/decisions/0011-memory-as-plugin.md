---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-09-21
deciders: shawncal, dmytrostruk
consulted: 
informed: 
---
# Move all Memory-related logic to separate Plugin

## Context and Problem Statement

Memory-related logic is located across different C# projects:

- `SemanticKernel.Abstractions`
  - `IMemoryStore`
  - `ISemanticTextMemory`
  - `MemoryRecord`
  - `NullMemory`
- `SemanticKernel.Core`
  - `MemoryConfiguration`
  - `SemanticTextMemory`
  - `VolatileMemoryStore`
- `Plugins.Core`
  - `TextMemoryPlugin`

Property `ISemanticTextMemory Memory` is also part of `Kernel` type, but kernel itself doesn't use it. This property is needed to inject Memory capabilities in Plugins. At the moment, `ISemanticTextMemory` interface is main dependency of `TextMemoryPlugin`, and in some examples `TextMemoryPlugin` is initialized as `new TextMemoryPlugin(kernel.Memory)`.

While this approach works for Memory, there is no way how to inject `MathPlugin` into other Plugin at the moment. Following the same approach and adding `Math` property to `Kernel` type is not scalable solution, as it's not possible to define separate properties for each available Plugin.

## Decision Drivers

1. Memory should not be a property of `Kernel` type if it's not used by the kernel.
2. Memory should be treated in the same way as other plugins or services, that may be required by specific Plugins.
3. There should be a way how to register Memory capability with attached Vector DB and inject that capability in Plugins that require it.

## Decision Outcome

Move all Memory-related logic to separate project called `Plugins.Memory`. This will allow to simplify Kernel logic and use Memory in places where it's needed (other Plugins).

High-level tasks:

1. Move Memory-related code to separate project.
2. Implement a way how to inject Memory in Plugins that require it.
3. Remove `Memory` property from `Kernel` type.
