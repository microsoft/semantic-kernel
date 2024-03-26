// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using RepoUtils;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example43_GetModelResult : BaseTest
{
    [Fact]
    public async Task GetTokenUsageMetadataAsync()
    {
        WriteLine("======== Inline Function Definition + Invocation ========");

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
        WriteLine(result.GetValue<string>());
        WriteLine(result.Metadata?["Usage"]?.AsJson());
        WriteLine();
    }

    [Fact]
    public async Task GetFullModelMetadataAsync()
    {
        WriteLine("======== Inline Function Definition + Invocation ========");

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
        WriteLine(result.GetValue<string>());
        WriteLine(result.Metadata?.AsJson());
        WriteLine();
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
            WriteLine(content.Metadata?.AsJson());
        }
    }

    public Example43_GetModelResult(ITestOutputHelper output) : base(output)
    {
    }
}
