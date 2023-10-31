---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: dmytrostruk
date: 2023-10-03
deciders: dmytrostruk
consulted:  semenshi, rbarreto, markwallace
informed: 
---
# Kernel Service Registration

## Context and Problem Statement

Plugins may have dependencies to support complex scenarios. For example, there is `TextMemoryPlugin`, which supports functions like `retrieve`, `recall`, `save`, `remove`. Constructor is implemented in following way:

```csharp
public TextMemoryPlugin(ISemanticTextMemory memory)
{
    this._memory = memory;
}
```

`TextMemoryPlugin` depends on `ISemanticTextMemory` interface. In similar way, other Plugins may have multiple dependencies and there should be a way how to resolve required dependencies manually or automatically.

At the moment, `ISemanticTextMemory` is a property of `IKernel` interface, which allows to inject `ISemanticTextMemory` into `TextMemoryPlugin` during Plugin initialization:

```csharp
kernel.ImportFunctions(new TextMemoryPlugin(kernel.Memory));
```

There should be a way how to support not only Memory-related interface, but any kind of service, which can be used in Plugin - `ISemanticTextMemory`, `IPromptTemplateEngine`, `IDelegatingHandlerFactory` or any other service.

## Considered Options

### Solution #1.1 (available by default)

User is responsible for all Plugins initialization and dependency resolution with **manual** approach.

```csharp
var memoryStore = new VolatileMemoryStore();
var embeddingGeneration = new OpenAITextEmbeddingGeneration(modelId, apiKey);
var semanticTextMemory = new SemanticTextMemory(memoryStore, embeddingGeneration);

var memoryPlugin = new TextMemoryPlugin(semanticTextMemory);

var kernel = Kernel.Builder.Build();

kernel.ImportFunctions(memoryPlugin);
```

Note: this is native .NET approach how to resolve service dependencies manually, and this approach should always be available by default. Any other solutions which could help to improve dependency resolution can be added on top of this approach.

### Solution #1.2 (available by default)

User is responsible for all Plugins initialization and dependency resolution with **dependency injection** approach.

```csharp
var serviceCollection = new ServiceCollection();

serviceCollection.AddTransient<IMemoryStore, VolatileMemoryStore>();
serviceCollection.AddTransient<ITextEmbeddingGeneration>(
    (serviceProvider) => new OpenAITextEmbeddingGeneration(modelId, apiKey));

serviceCollection.AddTransient<ISemanticTextMemory, SemanticTextMemory>();

var services = serviceCollection.BuildServiceProvider();

// In theory, TextMemoryPlugin can be also registered in DI container.
var memoryPlugin = new TextMemoryPlugin(services.GetService<ISemanticTextMemory>());

var kernel = Kernel.Builder.Build();

kernel.ImportFunctions(memoryPlugin);
```

Note: in similar way as Solution #1.1, this way should be supported out of the box. Users always can handle all the dependencies on their side and just provide required Plugins to Kernel.

### Solution #2.1

Custom service collection and service provider on Kernel level to simplify dependency resolution process, as addition to Solution #1.1 and Solution #1.2.

Interface `IKernel` will have its own service provider `KernelServiceProvider` with minimal functionality to get required service.

```csharp
public interface IKernelServiceProvider 
{
    T? GetService<T>(string? name = null);
} 

public interface IKernel 
{
    IKernelServiceProvider Services { get; }
}
```

```csharp
var kernel = Kernel.Builder
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithOpenAITextEmbeddingGenerationService(modelId, apiKey)
    .WithService<IMemoryStore, VolatileMemoryStore>(),
    .WithService<ISemanticTextMemory, SemanticTextMemory>()
    .Build();

var semanticTextMemory = kernel.Services.GetService<ISemanticTextMemory>();
var memoryPlugin = new TextMemoryPlugin(semanticTextMemory);

kernel.ImportFunctions(memoryPlugin);
```

Pros:

- No dependency on specific DI container library.
- Lightweight implementation.
- Possibility to register only those services that can be used by Plugins (isolation from host application).
- Possibility to register same interface multiple times by **name**.

Cons:

- Implementation and maintenance for custom DI container, instead of using already existing libraries.
- To import Plugin, it still needs to be initialized manually to inject specific service.

### Solution #2.2

This solution is an improvement for last disadvantage of Solution #2.1 to handle case, when Plugin instance should be initialized manually. This will require to add new way how to import Plugin into Kernel - not with object **instance**, but with object **type**. In this case, Kernel will be responsible for `TextMemoryPlugin` initialization and injection of all required dependencies from custom service collection.

```csharp
// Instead of this
var semanticTextMemory = kernel.Services.GetService<ISemanticTextMemory>();
var memoryPlugin = new TextMemoryPlugin(semanticTextMemory);

kernel.ImportFunctions(memoryPlugin);

// Use this
kernel.ImportFunctions<TextMemoryPlugin>();
```

### Solution #3

Instead of custom service collection and service provider in Kernel, use already existing DI library - `Microsoft.Extensions.DependencyInjection`.

```csharp
var serviceCollection = new ServiceCollection();

serviceCollection.AddTransient<IMemoryStore, VolatileMemoryStore>();
serviceCollection.AddTransient<ITextEmbeddingGeneration>(
    (serviceProvider) => new OpenAITextEmbeddingGeneration(modelId, apiKey));

serviceCollection.AddTransient<ISemanticTextMemory, SemanticTextMemory>();

var services = serviceCollection.BuildServiceProvider();

var kernel = Kernel.Builder
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithOpenAITextEmbeddingGenerationService(modelId, apiKey)
    .WithServices(services) // Pass all registered services from host application to Kernel
    .Build();

// Plugin Import - option #1
var semanticTextMemory = kernel.Services.GetService<ISemanticTextMemory>();
var memoryPlugin = new TextMemoryPlugin(semanticTextMemory);

kernel.ImportFunctions(memoryPlugin);

// Plugin Import - option #2
kernel.ImportFunctions<TextMemoryPlugin>();
```

Pros:

- No implementation is required for dependency resolution - just use already existing .NET library.
- The possibility to inject all registered services at once in already existing applications and use them as Plugin dependencies.

Cons:

- Additional dependency for Semantic Kernel package - `Microsoft.Extensions.DependencyInjection`.
- No possibility to include specific list of services (lack of isolation from host application).
- Possibility of `Microsoft.Extensions.DependencyInjection` version mismatch and runtime errors (e.g. users have `Microsoft.Extensions.DependencyInjection` `--version 2.0`  while Semantic Kernel uses `--version 6.0`)

## Decision Outcome

As for now, support Solution #1.1 and Solution #1.2 only, to keep Kernel as unit of single responsibility. Plugin dependencies should be resolved before passing Plugin instance to the Kernel.
