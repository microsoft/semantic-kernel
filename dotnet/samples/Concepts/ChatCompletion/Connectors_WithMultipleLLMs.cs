// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using xRetry;

namespace ChatCompletion;

public class Connectors_WithMultipleLLMs(ITestOutputHelper output) : BaseTest(output)
{
    private const string ChatPrompt = "Hello AI, what can you do for me?";
    /// <summary>
    /// Show how to run a prompt function and specify a specific service to use.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task RunAsync()
    {
        Kernel kernel = Kernel.CreateBuilder()
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

        // Preconfigured function settings
        await PreconfiguredFunctionSettingsByFirstModelIdAsync(kernel, ["gpt-4-1106-preview", TestConfiguration.AzureOpenAI.ChatModelId, TestConfiguration.OpenAI.ChatModelId]);
        await PreconfiguredFunctionSettingsByFirstServiceIdAsync(kernel, ["NotFound", "AzureOpenAIChat", "OpenAIChat"]);
        await PreconfiguredFunctionSettingsByModelIdAsync(kernel, TestConfiguration.OpenAI.ChatModelId);
        await PreconfiguredFunctionSettingsByServiceIdAsync(kernel, "AzureOpenAIChat");

        // Per invocation settings
        await InvocationSettingsByServiceIdAsync(kernel, "AzureOpenAIChat");
        await InvocationSettingsByFirstServiceIdAsync(kernel, ["NotFound", "AzureOpenAIChat", "OpenAIChat"]);
        await InvocationSettingsByModelIdAsync(kernel, TestConfiguration.OpenAI.ChatModelId);
        await InvocationSettingsByFirstModelIdAsync(kernel, ["gpt-4-1106-preview", TestConfiguration.AzureOpenAI.ChatModelId, TestConfiguration.OpenAI.ChatModelId]);
    }

    private async Task InvocationSettingsByServiceIdAsync(Kernel kernel, string serviceId)
    {
        Console.WriteLine($"======== Service Id: {serviceId} ========");

        var result = await kernel.InvokePromptAsync(ChatPrompt, new(new PromptExecutionSettings { ServiceId = serviceId }));

        Console.WriteLine(result.GetValue<string>());
    }

    private async Task InvocationSettingsByFirstServiceIdAsync(Kernel kernel, string[] serviceIds)
    {
        Console.WriteLine($"======== Service Ids: {string.Join(", ", serviceIds)} ========");

        var result = await kernel.InvokePromptAsync(ChatPrompt, new(serviceIds.Select(serviceId => new PromptExecutionSettings { ServiceId = serviceId })));

        Console.WriteLine(result.GetValue<string>());
    }

    private async Task InvocationSettingsByFirstModelIdAsync(Kernel kernel, string[] modelIds)
    {
        Console.WriteLine($"======== Model Ids: {string.Join(", ", modelIds)} ========");

        var result = await kernel.InvokePromptAsync(ChatPrompt, new(modelIds.Select((modelId, index) => new PromptExecutionSettings { ServiceId = $"service-{index}", ModelId = modelId })));

        Console.WriteLine(result.GetValue<string>());
    }

    private async Task InvocationSettingsByModelIdAsync(Kernel kernel, string modelId)
    {
        Console.WriteLine($"======== Model Id: {modelId} ========");

        var result = await kernel.InvokePromptAsync(ChatPrompt, new(new PromptExecutionSettings() { ModelId = modelId }));

        Console.WriteLine(result.GetValue<string>());
    }

    private async Task PreconfiguredFunctionSettingsByFirstServiceIdAsync(Kernel kernel, string[] serviceIds)
    {
        Console.WriteLine($"======== Service Ids: {string.Join(", ", serviceIds)} ========");

        var function = kernel.CreateFunctionFromPrompt(ChatPrompt, serviceIds.Select(serviceId => new PromptExecutionSettings { ServiceId = serviceId }));
        var result = await kernel.InvokeAsync(function);

        Console.WriteLine(result.GetValue<string>());
    }

    private async Task PreconfiguredFunctionSettingsByFirstModelIdAsync(Kernel kernel, string[] modelIds)
    {
        Console.WriteLine($"======== Model Ids: {string.Join(", ", modelIds)} ========");

        var function = kernel.CreateFunctionFromPrompt(ChatPrompt, modelIds.Select((modelId, index) => new PromptExecutionSettings { ServiceId = $"service-{index}", ModelId = modelId }));
        var result = await kernel.InvokeAsync(function);

        Console.WriteLine(result.GetValue<string>());
    }

    private async Task PreconfiguredFunctionSettingsByModelIdAsync(Kernel kernel, string modelId)
    {
        Console.WriteLine($"======== Model Id: {modelId} ========");

        var function = kernel.CreateFunctionFromPrompt(ChatPrompt);
        var result = await kernel.InvokeAsync(function, new(new PromptExecutionSettings { ModelId = modelId }));

        Console.WriteLine(result.GetValue<string>());
    }

    private async Task PreconfiguredFunctionSettingsByServiceIdAsync(Kernel kernel, string serviceId)
    {
        Console.WriteLine($"======== Service Id: {serviceId} ========");

        var function = kernel.CreateFunctionFromPrompt(ChatPrompt);
        var result = await kernel.InvokeAsync(function, new(new PromptExecutionSettings { ServiceId = serviceId }));

        Console.WriteLine(result.GetValue<string>());
    }
}
