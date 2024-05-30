// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ChatCompletion;

public class Connectors_WithMultipleLLMs(ITestOutputHelper output) : BaseTest(output)
{
    private const string ChatPrompt = "Hello AI, what can you do for me?";

    private static Kernel BuildKernel()
    {
        return Kernel.CreateBuilder()
                    .AddAzureOpenAIChatCompletion(
                        deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                        endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                        apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                        serviceId: "AzureOpenAIChat",
                        modelId: TestConfiguration.AzureOpenAI.ChatModelId)
                    .AddOpenAIChatCompletion(
                        modelId: TestConfiguration.OpenAI.ChatModelId,
                        apiKey: TestConfiguration.OpenAI.ApiKey,
                        serviceId: "OpenAIChat")
                    .Build();
    }

    /// <summary>
    /// Invoke the prompt function to run for a specific service id.
    /// </summary>
    /// <param name="serviceId">Service Id</param>
    [Theory]
    [InlineData("AzureOpenAIChat")]
    public async Task InvokePromptByServiceIdAsync(string serviceId)
    {
        var kernel = BuildKernel();
        Console.WriteLine($"======== Service Id: {serviceId} ========");

        var result = await kernel.InvokePromptAsync(ChatPrompt, new(new PromptExecutionSettings { ServiceId = serviceId }));

        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Invoke the prompt function to run for a specific model id.
    /// </summary>
    [Fact]
    private async Task InvokePromptByModelIdAsync()
    {
        var modelId = TestConfiguration.OpenAI.ChatModelId;
        var kernel = BuildKernel();
        Console.WriteLine($"======== Model Id: {modelId} ========");

        var result = await kernel.InvokePromptAsync(ChatPrompt, new(new PromptExecutionSettings() { ModelId = modelId }));

        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Invoke the prompt function to preferably run for a list specific service ids where the
    /// first service id that is found respecting the order of the options provided will be used.
    /// </summary>
    [Fact]
    public async Task InvokePromptFunctionWithFirstMatchingServiceIdAsync()
    {
        string[] serviceIds = ["NotFound", "AzureOpenAIChat", "OpenAIChat"];
        var kernel = BuildKernel();
        Console.WriteLine($"======== Service Ids: {string.Join(", ", serviceIds)} ========");

        var result = await kernel.InvokePromptAsync(ChatPrompt, new(serviceIds.Select(serviceId => new PromptExecutionSettings { ServiceId = serviceId })));

        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Invoke the prompt function to preferably run for a list of specific model ids where the
    /// first model id that is found respecting the order of the options provided will be used.
    /// </summary>
    [Fact]
    public async Task InvokePromptFunctionWithFirstMatchingModelIdAsync()
    {
        string[] modelIds = ["gpt-4-1106-preview", TestConfiguration.AzureOpenAI.ChatModelId, TestConfiguration.OpenAI.ChatModelId];
        var kernel = BuildKernel();
        Console.WriteLine($"======== Model Ids: {string.Join(", ", modelIds)} ========");

        var result = await kernel.InvokePromptAsync(ChatPrompt, new(modelIds.Select((modelId, index) => new PromptExecutionSettings { ServiceId = $"service-{index}", ModelId = modelId })));

        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Create a function with a predefined configuration and invoke at later moment.
    /// </summary>
    [Fact]
    public async Task InvokePreconfiguredFunctionWithFirstMatchingServiceIdAsync()
    {
        string[] serviceIds = ["NotFound", "AzureOpenAIChat", "OpenAIChat"];
        var kernel = BuildKernel();
        Console.WriteLine($"======== Service Ids: {string.Join(", ", serviceIds)} ========");

        var function = kernel.CreateFunctionFromPrompt(ChatPrompt, serviceIds.Select(serviceId => new PromptExecutionSettings { ServiceId = serviceId }));
        var result = await kernel.InvokeAsync(function);

        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Create a function with a predefined configuration to preferably run for a list specific model ids where the
    /// first model id that is found respecting the order of the options provided will be used.
    /// </summary>
    [Fact]
    public async Task InvokePreconfiguredFunctionWithFirstMatchingModelIdAsync()
    {
        string[] modelIds = ["gpt-4-1106-preview", TestConfiguration.AzureOpenAI.ChatModelId, TestConfiguration.OpenAI.ChatModelId];
        var kernel = BuildKernel();

        Console.WriteLine($"======== Model Ids: {string.Join(", ", modelIds)} ========");

        var function = kernel.CreateFunctionFromPrompt(ChatPrompt, modelIds.Select((modelId, index) => new PromptExecutionSettings { ServiceId = $"service-{index}", ModelId = modelId }));
        var result = await kernel.InvokeAsync(function);

        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Create a function with a predefined configuration to run for a specific model id.
    /// </summary>
    [Fact]
    public async Task InvokePreconfiguredFunctionByModelIdAsync()
    {
        var modelId = TestConfiguration.OpenAI.ChatModelId;
        var kernel = BuildKernel();
        Console.WriteLine($"======== Model Id: {modelId} ========");

        var function = kernel.CreateFunctionFromPrompt(ChatPrompt);
        var result = await kernel.InvokeAsync(function, new(new PromptExecutionSettings { ModelId = modelId }));

        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Create a function with a predefined configuration to run for a specific service id.
    /// </summary>
    /// <param name="serviceId">Service Id</param>
    [Theory]
    [InlineData("AzureOpenAIChat")]
    public async Task InvokePreconfiguredFunctionByServiceIdAsync(string serviceId)
    {
        var kernel = BuildKernel();
        Console.WriteLine($"======== Service Id: {serviceId} ========");

        var function = kernel.CreateFunctionFromPrompt(ChatPrompt);
        var result = await kernel.InvokeAsync(function, new(new PromptExecutionSettings { ServiceId = serviceId }));

        Console.WriteLine(result.GetValue<string>());
    }
}
