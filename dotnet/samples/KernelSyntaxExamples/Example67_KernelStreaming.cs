// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

// This example shows how to use multiple prompt template formats.
public class Example67_KernelStreaming : BaseTest
{
    /// <summary>
    /// Show how to combine multiple prompt template factories.
    /// </summary>
    [Fact]
    public async Task RunAsync()
    {
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string chatModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || chatModelId == null || endpoint == null)
        {
            this._output.WriteLine("Azure endpoint, apiKey, deploymentName or modelId not found. Skipping example.");
            return;
        }

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey,
                modelId: chatModelId)
            .Build();

        var funnyParagraphFunction = kernel.CreateFunctionFromPrompt("Write a funny paragraph about streaming", new OpenAIPromptExecutionSettings() { MaxTokens = 100, Temperature = 0.4, TopP = 1 });

        var roleDisplayed = false;

        this._output.WriteLine("\n===  Prompt Function - Streaming ===\n");

        string fullContent = string.Empty;
        // Streaming can be of any type depending on the underlying service the function is using.
        await foreach (var update in kernel.InvokeStreamingAsync<OpenAIStreamingChatMessageContent>(funnyParagraphFunction))
        {
            // You will be always able to know the type of the update by checking the Type property.
            if (!roleDisplayed && update.Role.HasValue)
            {
                this._output.WriteLine($"Role: {update.Role}");
                fullContent += $"Role: {update.Role}\n";
                roleDisplayed = true;
            }

            if (update.Content is { Length: > 0 })
            {
                fullContent += update.Content;
                this._output.Write(update.Content);
            }
        }

        this._output.WriteLine("\n------  Streamed Content ------\n");
        this._output.WriteLine(fullContent);
    }

    public Example67_KernelStreaming(ITestOutputHelper output) : base(output)
    {
    }
}
