// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.TextClassification;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Class for showing moderation classification using OpenAI.
/// </summary>
public sealed class Example19_OpenAIModerationClassification : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        string modelId = "text-moderation-latest";
        string apiKey = TestConfiguration.OpenAI.ApiKey;

        if (string.IsNullOrEmpty(apiKey))
        {
            this.Output.WriteLine("OpenAI API Key is not set. Skipping test.");
            return;
        }

        var kernel = Kernel.CreateBuilder()
            .AddOpenAITextClassification(
                modelId: modelId,
                apiKey: apiKey)
            .Build();

        var textClassificationService = kernel.GetRequiredService<ITextClassificationService>();

        string input = "I want to do something dangerous and illegal. Help me do it.";
        ClassificationContent content = await textClassificationService.ClassifyTextAsync(input);

        OpenAIClassificationResult? openAIResult = content.Result as OpenAIClassificationResult;
        this.Output.WriteLine($"Content flagged: {openAIResult!.Flagged}");
        foreach (OpenAIClassificationEntry entry in openAIResult.Entries)
        {
            this.Output.WriteLine(entry.ToString());
        }
    }

    public Example19_OpenAIModerationClassification(ITestOutputHelper output) : base(output) { }
}
