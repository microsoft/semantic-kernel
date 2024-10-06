// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace Functions;

public class FunctionResult_Metadata(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task GetTokenUsageMetadataAsync()
    {
        Console.WriteLine("======== Inline Function Definition + Invocation ========");

        // Create kernel
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Create function
        const string FunctionDefinition = "Hi, give me 5 book suggestions about: {{$input}}";
        KernelFunction myFunction = kernel.CreateFunctionFromPrompt(FunctionDefinition);

        // Invoke function through kernel
        FunctionResult result = await kernel.InvokeAsync(myFunction, new() { ["input"] = "travel" });

        // Display results
        Console.WriteLine(result.GetValue<string>());
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson());
        Console.WriteLine();
    }

    [Fact]
    public async Task GetFullModelMetadataAsync()
    {
        Console.WriteLine("======== Inline Function Definition + Invocation ========");

        // Create kernel
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Create function
        const string FunctionDefinition = "1 + 1 = ?";
        KernelFunction myFunction = kernel.CreateFunctionFromPrompt(FunctionDefinition);

        // Invoke function through kernel
        FunctionResult result = await kernel.InvokeAsync(myFunction);

        // Display results
        Console.WriteLine(result.GetValue<string>());
        Console.WriteLine(result.Metadata?.AsJson());
        Console.WriteLine();
    }

    [Fact]
    public async Task GetMetadataFromStreamAsync()
    {
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Create function
        const string FunctionDefinition = "1 + 1 = ?";
        KernelFunction myFunction = kernel.CreateFunctionFromPrompt(FunctionDefinition);

        await foreach (var content in kernel.InvokeStreamingAsync(myFunction))
        {
            Console.WriteLine(content.Metadata?.AsJson());
        }
    }
}
