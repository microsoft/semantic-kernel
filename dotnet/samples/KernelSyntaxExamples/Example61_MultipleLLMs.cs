// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using xRetry;
using Xunit.Abstractions;

namespace Examples;

public class Example61_MultipleLLMs : BaseTest
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
        await RunByFirstModelIdAsync(kernel, "gpt-4-1106-preview", TestConfiguration.AzureOpenAI.ChatModelId, TestConfiguration.OpenAI.ChatModelId);
    }

    private async Task RunByServiceIdAsync(Kernel kernel, string serviceId)
    {
        WriteLine($"======== Service Id: {serviceId} ========");

        var prompt = "Hello AI, what can you do for me?";

        KernelArguments arguments = new();
        arguments.ExecutionSettings = new Dictionary<string, PromptExecutionSettings>()
        {
            { serviceId, new PromptExecutionSettings() }
        };
        var result = await kernel.InvokePromptAsync(prompt, arguments);
        WriteLine(result.GetValue<string>());
    }

    private async Task RunByModelIdAsync(Kernel kernel, string modelId)
    {
        WriteLine($"======== Model Id: {modelId} ========");

        var prompt = "Hello AI, what can you do for me?";

        var result = await kernel.InvokePromptAsync(
           prompt,
           new(new PromptExecutionSettings()
           {
               ModelId = modelId
           }));
        WriteLine(result.GetValue<string>());
    }

    private async Task RunByFirstModelIdAsync(Kernel kernel, params string[] modelIds)
    {
        WriteLine($"======== Model Ids: {string.Join(", ", modelIds)} ========");

        var prompt = "Hello AI, what can you do for me?";

        var modelSettings = new Dictionary<string, PromptExecutionSettings>();
        foreach (var modelId in modelIds)
        {
            modelSettings.Add(modelId, new PromptExecutionSettings() { ModelId = modelId });
        }
        var promptConfig = new PromptTemplateConfig(prompt) { Name = "HelloAI", ExecutionSettings = modelSettings };

        var function = kernel.CreateFunctionFromPrompt(promptConfig);

        var result = await kernel.InvokeAsync(function);
        WriteLine(result.GetValue<string>());
    }

    public Example61_MultipleLLMs(ITestOutputHelper output) : base(output)
    {
    }
}
