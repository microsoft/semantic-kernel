// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;

#pragma warning disable format // Format item can be simplified
#pragma warning disable CA1861 // Avoid constant arrays as arguments

namespace TextGeneration;

// The following example shows how to use Semantic Kernel with Ollama Text Generation API.
public class Ollama_TextGenerationStreaming(ITestOutputHelper helper) : BaseTest(helper)
{
    [Fact]
    public async Task RunKernelStreamingExampleAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        string model = TestConfiguration.Ollama.ModelId;

        Console.WriteLine($"\n======== Ollama {model} streaming example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddOllamaTextGeneration(
                endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
                modelId: model)
            .Build();

        await foreach (string text in kernel.InvokePromptStreamingAsync<string>("Question: {{$input}}; Answer:", new() { ["input"] = "What is New York?" }))
        {
            Console.Write(text);
        }
    }

    [Fact]
    public async Task RunServiceStreamingExampleAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        string model = TestConfiguration.Ollama.ModelId;

        Console.WriteLine($"\n======== Ollama {model} streaming example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddOllamaTextGeneration(
                endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
                modelId: model)
            .Build();

        var service = kernel.GetRequiredService<ITextGenerationService>();

        await foreach (var content in service.GetStreamingTextContentsAsync("Question: What is New York?; Answer:"))
        {
            Console.Write(content);
        }
    }
}
