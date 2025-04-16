// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;

namespace KernelExamples;

/// <summary>
/// This sample shows how to use a custom AI service selector to select a specific model by matching the model id.
/// </summary>
public class CustomAIServiceSelector(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task UsingCustomSelectToSelectServiceByMatchingModelId()
    {
        Console.WriteLine($"======== {nameof(UsingCustomSelectToSelectServiceByMatchingModelId)} ========");

        // Use the custom AI service selector to select any registered service starting with "gpt" on it's model id
        var customSelector = new GptAIServiceSelector(modelNameStartsWith: "gpt", this.Output);

        // Build a kernel with multiple chat services
        var builder = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                serviceId: "AzureOpenAIChat",
                modelId: "o1-mini")
            .AddOpenAIChatCompletion(
                modelId: "o1-mini",
                apiKey: TestConfiguration.OpenAI.ApiKey,
                serviceId: "OpenAIChat");

        // The kernel also allows you to use a IChatClient chat service as well
        builder.Services
            .AddSingleton<IAIServiceSelector>(customSelector)
            .AddKeyedChatClient("OpenAIChatClient", new OpenAI.OpenAIClient(TestConfiguration.OpenAI.ApiKey)
                .GetChatClient("gpt-4o")
                .AsIChatClient()); // Add a IChatClient to the kernel

        Kernel kernel = builder.Build();

        // This invocation is done with the model selected by the custom selector
        var prompt = "Hello AI, what can you do for me?";
        var result = await kernel.InvokePromptAsync(prompt);
        Console.WriteLine(result.GetValue<string>());
    }

    /// <summary>
    /// Custom AI service selector that selects a GPT model.
    /// This selector just naively selects the first service that provides
    /// a completion model whose name starts with "gpt". But this logic could
    /// be as elaborate as needed to apply your own selection criteria.
    /// </summary>
    private sealed class GptAIServiceSelector(string modelNameStartsWith, ITestOutputHelper output) : IAIServiceSelector, IChatClientSelector
    {
        private readonly ITestOutputHelper _output = output;
        private readonly string _modelNameStartsWith = modelNameStartsWith;

        private bool TrySelect<T>(
            Kernel kernel, KernelFunction function, KernelArguments arguments,
            [NotNullWhen(true)] out T? service, out PromptExecutionSettings? serviceSettings) where T : class
        {
            foreach (var serviceToCheck in kernel.GetAllServices<T>())
            {
                string? serviceModelId = null;
                string? endpoint = null;

                if (serviceToCheck is IAIService aiService)
                {
                    serviceModelId = aiService.GetModelId();
                    endpoint = aiService.GetEndpoint();
                }
                else if (serviceToCheck is IChatClient chatClient)
                {
                    var metadata = chatClient.GetService<ChatClientMetadata>();
                    serviceModelId = metadata?.DefaultModelId;
                    endpoint = metadata?.ProviderUri?.ToString();
                }

                // Find the first service that has a model id that starts with "gpt"
                if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith(this._modelNameStartsWith, StringComparison.OrdinalIgnoreCase))
                {
                    this._output.WriteLine($"Selected model: {serviceModelId} {endpoint}");
                    service = serviceToCheck;
                    serviceSettings = new OpenAIPromptExecutionSettings();
                    return true;
                }
            }

            service = null;
            serviceSettings = null;
            return false;
        }

        /// <inheritdoc/>
        public bool TrySelectAIService<T>(
            Kernel kernel,
            KernelFunction function,
            KernelArguments arguments,
            [NotNullWhen(true)] out T? service,
            out PromptExecutionSettings? serviceSettings) where T : class, IAIService
            => this.TrySelect(kernel, function, arguments, out service, out serviceSettings);

        /// <inheritdoc/>
        public bool TrySelectChatClient<T>(
            Kernel kernel,
            KernelFunction function,
            KernelArguments arguments,
            [NotNullWhen(true)] out T? service,
            out PromptExecutionSettings? serviceSettings) where T : class, IChatClient
            => this.TrySelect(kernel, function, arguments, out service, out serviceSettings);
    }
}
