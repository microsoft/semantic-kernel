// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace ChatCompletion;

/// <summary>
/// Demonstrates reading token usage from a Google chat response returned by the kernel.
/// </summary>
public sealed class Google_GeminiGetModelResult(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GetTokenUsageMetadataUsingGoogleAI()
    {
        Console.WriteLine("======== Google AI - Inline Function Definition + Invocation ========");

        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);
        Assert.NotNull(TestConfiguration.GoogleAI.Gemini.ModelId);

        using var googleClient = new Google.GenAI.Client(apiKey: TestConfiguration.GoogleAI.ApiKey);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddChatClient(googleClient.AsIChatClient(TestConfiguration.GoogleAI.Gemini.ModelId));
        Kernel kernel = builder.Build();

        await this.DisplayTokenUsageAsync(kernel);
    }

    [Fact]
    public async Task GetTokenUsageMetadata()
    {
        Console.WriteLine("======== Inline Function Definition + Invocation ========");

        Assert.NotNull(TestConfiguration.VertexAI.Location);
        Assert.NotNull(TestConfiguration.VertexAI.ProjectId);
        Assert.NotNull(TestConfiguration.VertexAI.Gemini.ModelId);

        // The Google SDK discovers application default credentials and refreshes tokens automatically.
        using var googleClient = new Google.GenAI.Client(
            vertexAI: true,
            project: TestConfiguration.VertexAI.ProjectId,
            location: TestConfiguration.VertexAI.Location);
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddChatClient(googleClient.AsIChatClient(TestConfiguration.VertexAI.Gemini.ModelId));
        Kernel kernel = builder.Build();

        await this.DisplayTokenUsageAsync(kernel);
    }

    private async Task DisplayTokenUsageAsync(Kernel kernel)
    {
        string prompt = "Hi, give me 5 book suggestions about: travel";

        // Invoke function through kernel
        FunctionResult result = await kernel.InvokePromptAsync(prompt);

        // Display results
        var response = result.GetValue<ChatResponse>();
        Console.WriteLine(result.GetValue<string>());
        Console.WriteLine($"Input tokens: {response?.Usage?.InputTokenCount}");
        Console.WriteLine($"Output tokens: {response?.Usage?.OutputTokenCount}");
        Console.WriteLine($"Total tokens: {response?.Usage?.TotalTokenCount}");
    }
}
