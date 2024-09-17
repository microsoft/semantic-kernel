// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextGeneration;
using xRetry;

#pragma warning disable format // Format item can be simplified
#pragma warning disable CA1861 // Avoid constant arrays as arguments

namespace TextGeneration;

// The following example shows how to use Semantic Kernel with Ollama Text Generation API.
public class Ollama_TextGeneration(ITestOutputHelper helper) : BaseTest(helper)
{
    [Fact]
    public async Task KernelPromptAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        Console.WriteLine("\n======== Ollama Text Generation example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddOllamaTextGeneration(
                endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
                modelId: TestConfiguration.Ollama.ModelId)
            .Build();

        var questionAnswerFunction = kernel.CreateFunctionFromPrompt("Question: {{$input}}; Answer:");

        var result = await kernel.InvokeAsync(questionAnswerFunction, new() { ["input"] = "What is New York?" });

        Console.WriteLine(result.GetValue<string>());
    }

    [Fact]
    public async Task ServicePromptAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        Console.WriteLine("\n======== Ollama Text Generation example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddOllamaTextGeneration(
                endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
                modelId: TestConfiguration.Ollama.ModelId)
            .Build();

        var service = kernel.GetRequiredService<ITextGenerationService>();
        var result = await service.GetTextContentAsync("Question: What is New York?; Answer:");

        Console.WriteLine(result);
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task RunStreamingExampleAsync()
    {
        Assert.NotNull(TestConfiguration.Ollama.ModelId);

        string model = TestConfiguration.Ollama.ModelId;

        Console.WriteLine($"\n======== HuggingFace {model} streaming example ========\n");

        Kernel kernel = Kernel.CreateBuilder()
            .AddOllamaTextGeneration(
                endpoint: new Uri(TestConfiguration.Ollama.Endpoint),
                modelId: TestConfiguration.Ollama.ModelId)
            .Build();

        var questionAnswerFunction = kernel.CreateFunctionFromPrompt("Question: {{$input}}; Answer:");

        await foreach (string text in kernel.InvokePromptStreamingAsync<string>("Question: {{$input}}; Answer:", new() { ["input"] = "What is New York?" }))
        {
            Console.Write(text);
        }
    }
}
