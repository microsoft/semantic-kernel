// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using RepoUtils;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// Represents an example class for Gemini Embedding Generation with volatile memory store.
/// </summary>
public class Example94_GeminiGetModelResult : BaseTest
{
    [Fact]
    public async Task GetTokenUsageMetadataAsync()
    {
        WriteLine("======== Inline Function Definition + Invocation ========");

        // Create kernel
        Kernel kernel = Kernel.CreateBuilder()
            .AddVertexAIGeminiChatCompletion(
                  modelId: TestConfiguration.VertexAI.Gemini.ModelId,
                  bearerKey: TestConfiguration.VertexAI.BearerKey,
                  location: TestConfiguration.VertexAI.Location,
                  projectId: TestConfiguration.VertexAI.ProjectId)
            .Build();

        // Create function
        const string FunctionDefinition = "Hi, give me 5 book suggestions about: {{$input}}";
        KernelFunction myFunction = kernel.CreateFunctionFromPrompt(FunctionDefinition);

        // Invoke function through kernel
        FunctionResult result = await kernel.InvokeAsync(myFunction, new() { ["input"] = "travel" });

        // Display results
        var geminiMetadata = result.Metadata as GeminiMetadata;
        WriteLine(result.GetValue<string>());
        WriteLine(geminiMetadata?.AsJson());
    }

    public Example94_GeminiGetModelResult(ITestOutputHelper output) : base(output)
    {
    }
}
