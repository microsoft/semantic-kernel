// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Examples;

/// <summary>
/// This example demonstrates how to add AI services to a kernel as described at
/// https://learn.microsoft.com/semantic-kernel/agents/kernel/adding-services
/// </summary>
public class AIServices(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task RunAsync()
    {
        Console.WriteLine("======== AI Services ========");

        string? endpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string? modelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string? textModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string? apiKey = TestConfiguration.AzureOpenAI.ApiKey;

        if (endpoint is null || modelId is null || textModelId is null || apiKey is null)
        {
            Console.WriteLine("Azure OpenAI credentials not found. Skipping example.");

            return;
        }

        string? openAImodelId = TestConfiguration.OpenAI.ChatModelId;
        string? openAItextModelId = TestConfiguration.OpenAI.ChatModelId;
        string? openAIapiKey = TestConfiguration.OpenAI.ApiKey;

        if (openAImodelId is null || openAItextModelId is null || openAIapiKey is null)
        {
            Console.WriteLine("OpenAI credentials not found. Skipping example.");

            return;
        }

        // Create a kernel with an Azure OpenAI chat completion service
        // <TypicalKernelCreation>
        Kernel kernel = Kernel.CreateBuilder()
                              .AddAzureOpenAIChatCompletion(modelId, endpoint, apiKey)
                              .Build();
        // </TypicalKernelCreation>

        // You could instead create a kernel with a legacy Azure OpenAI text completion service
        // <TextCompletionKernelCreation>
        kernel = Kernel.CreateBuilder()
                       .AddAzureOpenAITextGeneration(textModelId, endpoint, apiKey)
                       .Build();
        // </TextCompletionKernelCreation>

        // You can also create a kernel with a (non-Azure) OpenAI chat completion service
        // <OpenAIKernelCreation>
        kernel = Kernel.CreateBuilder()
                       .AddOpenAIChatCompletion(openAImodelId, openAIapiKey)
                       .Build();
        // </OpenAIKernelCreation>

        // Or a kernel with a legacy OpenAI text completion service
        // <OpenAITextCompletionKernelCreation>
        kernel = Kernel.CreateBuilder()
                       .AddOpenAITextGeneration(openAItextModelId, openAIapiKey)
                       .Build();
        // </OpenAITextCompletionKernelCreation>
    }
}
