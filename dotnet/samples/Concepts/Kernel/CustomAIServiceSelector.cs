// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;

namespace KernelExamples;

public class CustomAIServiceSelector(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to use a custom AI service selector to select a specific model
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        Console.WriteLine($"======== {nameof(CustomAIServiceSelector)} ========");

        // Build a kernel with multiple chat completion services
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
        builder.Services
            .AddSingleton<IAIServiceSelector>(new GptAIServiceSelector(this.Output)) // Use the custom AI service selector to select the GPT model
            .AddChatClient(new OpenAI.OpenAIClient(TestConfiguration.OpenAI.ApiKey)
                .AsChatClient("gpt-4o")); // Add a IChatClient to the kernel

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
    private sealed class GptAIServiceSelector(ITestOutputHelper output) : IAIServiceSelector, IServiceSelector
    {
        private readonly ITestOutputHelper _output = output;

        public bool TrySelect<T>(
            Kernel kernel, KernelFunction function, KernelArguments arguments,
            [NotNullWhen(true)] out T? service, out PromptExecutionSettings? serviceSettings) where T : class
        {
            foreach (var serviceToCheck in kernel.GetAllServices<T>())
            {
                if (serviceToCheck is IAIService aiService)
                {
                    // Find the first service that has a model id that starts with "gpt"
                    var serviceModelId = aiService.GetModelId();
                    var endpoint = aiService.GetEndpoint();

                    if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith("gpt", StringComparison.OrdinalIgnoreCase))
                    {
                        this._output.WriteLine($"Selected model: {serviceModelId} {endpoint}");
                        service = serviceToCheck;
                        serviceSettings = new OpenAIPromptExecutionSettings();
                        return true;
                    }
                }
                else if (serviceToCheck is IChatClient chatClient)
                {
                    var metadata = chatClient.GetService<ChatClientMetadata>();

                    // Find the first service that has a model id that starts with "gpt"
                    var serviceModelId = metadata?.ModelId;
                    var endpoint = metadata?.ProviderUri;

                    if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith("gpt", StringComparison.OrdinalIgnoreCase))
                    {
                        this._output.WriteLine($"Selected model: {serviceModelId} {endpoint}");
                        service = serviceToCheck;
                        serviceSettings = new OpenAIPromptExecutionSettings();
                        return true;
                    }
                }
            }

            service = null;
            serviceSettings = null;
            return false;
        }

        public bool TrySelectAIService<T>(
            Kernel kernel,
            KernelFunction function,
            KernelArguments arguments,
            [NotNullWhen(true)] out T? service,
            out PromptExecutionSettings? serviceSettings) where T : class, IAIService
            => this.TrySelect(kernel, function, arguments, out service, out serviceSettings);
    }
}
