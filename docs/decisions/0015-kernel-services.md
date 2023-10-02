# Proposal for Kernel Services 

Setting up the Kernel services can be done following the pattern for DI containers or using Helper `With` methods

This approach is straight forward and easy to understand for developers familiar with DI containers and C#.

```csharp
    IKernel kernel = new KernelBuilder()
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)

    // You can add the services using the With extension helper methods
    .WithOpenAIChatCompletionService(
        modelId: openAIModelId,
        apiKey: openAIApiKey)

    // Or you can also add manually the services
    .Services.AddTransient<IChatCompletion, AzureChatCompletion>(cfg => { 
        cfg.ModelId = openAIModelId; 
        cfg.ApiKey = openAIApiKey; 
    })

    // You can add multiple services of the same interface
    .Services.AddSingleton<IMemoryStore, VolatileMemoryStore>(cfg => ...) 
    .Services.AddSingleton<IMemoryStore, AzureCognitiveSearchMemoryStore>(cfg => ...)

    .Services.AddSingleton<IPromptTemplateEngine, PromptTemplateEngine>(cfg => ...)
    .Services.AddSingleton<IPromptTemplateEngine, MyPromptTemplateEngine>(cfg => ...)

    .UseConfiguration(configuration)
    .Build();
```

Once the Kernel is built the services will be available when running the functions on demand thru 
an inteligent Kernel DI service injection.

```csharp

public class LocalExamplePlugin {

    // Kernel will inject the service by interface in the function call
    [SKFunction]
    public void MyFunction1(ISemanticTextMemory textMemoryService, ILogger<LocalExamplePlugin> logger) 
    {
        // Do something with the service and logger
    }

    // Kernel will inject the service by concrete type in the function call
    [SKFunction]
    public void MyFunction2(AzureOpenAIImageGeneration azureConcreteImageGeneration, ILogger<LocalExamplePlugin> logger) 
    {
        // Do something with the service and logger
    }

    // Kernel will inject the SKContext in the function call which can be used to get the service instance
    [SKFunction]
    public void MyFunction3(SKContext executionContext) 
    {
        var textMemoryService = executionContext.GetService<ISemanticTextMemory>();
        var logger = executionContext.GetService<ILogger<LocalExamplePlugin>>();
        // Do something with the service
    }
}

var testFunctions = kernel.ImportFunctions(new LocalExamplePlugin(), "test");
var kernelResult = await kernel.RunAsync(testFunctions["MyFunction1"]);
```