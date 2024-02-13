// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/**
 * The following example shows how to use Semantic Kernel with streaming text completion.
 *
 * This example will NOT work with regular chat completion models. It will only work with
 * text completion models.
 *
 * Note that all text generation models are deprecated by OpenAI and will be removed in a future release.
 *
 * Refer to example 33 for streaming chat completion.
 */
public class Example32_StreamingCompletion : BaseTest
{
    [Fact]
    public Task AzureOpenAITextGenerationStreamAsync()
    {
        WriteLine("======== Azure OpenAI - Text Completion - Raw Streaming ========");

        var textGeneration = new AzureOpenAITextGenerationService(
            deploymentName: TestConfiguration.AzureOpenAI.DeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ModelId);

        return this.TextGenerationStreamAsync(textGeneration);
    }

    [Fact]
    public Task OpenAITextGenerationStreamAsync()
    {
        WriteLine("======== Open AI - Text Completion - Raw Streaming ========");

        var textGeneration = new OpenAITextGenerationService("gpt-3.5-turbo-instruct", TestConfiguration.OpenAI.ApiKey);

        return this.TextGenerationStreamAsync(textGeneration);
    }

    private async Task TextGenerationStreamAsync(ITextGenerationService textGeneration)
    {
        var executionSettings = new OpenAIPromptExecutionSettings()
        {
            MaxTokens = 100,
            FrequencyPenalty = 0,
            PresencePenalty = 0,
            Temperature = 1,
            TopP = 0.5
        };

        var prompt = "Write one paragraph why AI is awesome";

        WriteLine("Prompt: " + prompt);
        await foreach (var content in textGeneration.GetStreamingTextContentsAsync(prompt, executionSettings))
        {
            Write(content);
        }

        WriteLine();
    }

    public Example32_StreamingCompletion(ITestOutputHelper output) : base(output)
    {
    }
}
