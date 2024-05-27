// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using xRetry;

namespace ChatCompletion;

public class Connectors_WithMultipleLLMs(ITestOutputHelper output) : BaseTest(output)
{
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

        await RunByServiceIdAsync(kernel, "AzureOpenAIChat");
        await RunByModelIdAsync(kernel, TestConfiguration.OpenAI.ChatModelId);
        await RunByFirstModelIdAsync(kernel, ["gpt-4-1106-preview", TestConfiguration.AzureOpenAI.ChatModelId, TestConfiguration.OpenAI.ChatModelId]);
        await RunByFirstServiceIdAsync(kernel, ["NotFound", "AzureOpenAIChat", "OpenAIChat"]);
    }

    private async Task RunByServiceIdAsync(Kernel kernel, string serviceId)
    {
        Console.WriteLine($"======== Service Id: {serviceId} ========");

        var prompt = "Hello AI, what can you do for me?";

        var result = await kernel.InvokePromptAsync(prompt, new(new PromptExecutionSettings { ServiceId = serviceId }));

        Console.WriteLine(result.GetValue<string>());
    }

    private async Task RunByFirstServiceIdAsync(Kernel kernel, string[] serviceIds)
    {
        Console.WriteLine($"======== Service Ids: {string.Join(", ", serviceIds)} ========");

        var prompt = "Hello AI, what can you do for me?";

        var function = kernel.CreateFunctionFromPrompt(prompt, serviceIds.Select(serviceId => new PromptExecutionSettings { ServiceId = serviceId }));

        var result = await kernel.InvokeAsync(function);

        Console.WriteLine(result.GetValue<string>());
    }

    private async Task RunByModelIdAsync(Kernel kernel, string modelId)
    {
        Console.WriteLine($"======== Model Id: {modelId} ========");

        var prompt = "Hello AI, what can you do for me?";

        var result = await kernel.InvokePromptAsync(
           prompt,
           new(new PromptExecutionSettings()
           {
               ModelId = modelId
           }));
        Console.WriteLine(result.GetValue<string>());
    }

    private async Task RunByFirstModelIdAsync(Kernel kernel, string[] modelIds)
    {
        Console.WriteLine($"======== Model Ids: {string.Join(", ", modelIds)} ========");

        var prompt = "Hello AI, what can you do for me?";

        var function = kernel.CreateFunctionFromPrompt(prompt, modelIds.Select((modelId, index) => new PromptExecutionSettings { ServiceId = $"service-{index}", ModelId = modelId }));

        var result = await kernel.InvokeAsync(function);
        Console.WriteLine(result.GetValue<string>());
    }
}
