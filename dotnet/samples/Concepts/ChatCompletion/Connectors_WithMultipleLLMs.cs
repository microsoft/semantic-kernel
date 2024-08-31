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
    /// Shows how to invoke a prompt and specify the service id of the preferred AI service. When the prompt is executed the AI Service with the matching service id will be selected.
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
    /// Shows how to invoke a prompt and specify the model id of the preferred AI service. When the prompt is executed the AI Service with the matching model id will be selected.
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
    /// Shows how to invoke a prompt and specify the service ids of the preferred AI services.
    /// When the prompt is executed the AI Service will be selected based on the order of the provided service ids.
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
    /// Shows how to invoke a prompt and specify the model ids of the preferred AI services.
    /// When the prompt is executed the AI Service will be selected based on the order of the provided model ids.
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
    /// Shows how to create a KernelFunction from a prompt and specify the service ids of the preferred AI services.
    /// When the function is invoked the AI Service will be selected based on the order of the provided service ids.
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
    /// Shows how to create a KernelFunction from a prompt and specify the model ids of the preferred AI services.
    /// When the function is invoked the AI Service will be selected based on the order of the provided model ids.
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
    /// Shows how to invoke a KernelFunction and specify the model id of the AI Service the function will use.
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
    /// Shows how to invoke a KernelFunction and specify the service id of the AI Service the function will use.
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

    /// <summary>
    /// Shows when specifying a non-existent ServiceId the kernel throws an exception.
    /// </summary>
    /// <param name="serviceId">Service Id</param>
    [Theory]
    [InlineData("NotFound")]
    public async Task InvokePromptByNonExistingServiceIdThrowsExceptionAsync(string serviceId)
    {
        var kernel = BuildKernel();
        Console.WriteLine($"======== Service Id: {serviceId} ========");

        await Assert.ThrowsAsync<KernelException>(async () => await kernel.InvokePromptAsync(ChatPrompt, new(new PromptExecutionSettings { ServiceId = serviceId })));
    }

    /// <summary>
    /// Shows how in the execution settings when no model id is found it falls back to the default service.
    /// </summary>
    /// <param name="modelId">Model Id</param>
    [Theory]
    [InlineData("NotFound")]
    public async Task InvokePromptByNonExistingModelIdUsesDefaultServiceAsync(string modelId)
    {
        var kernel = BuildKernel();
        Console.WriteLine($"======== Model Id: {modelId} ========");

        await kernel.InvokePromptAsync(ChatPrompt, new(new PromptExecutionSettings { ModelId = modelId }));
    }
}
