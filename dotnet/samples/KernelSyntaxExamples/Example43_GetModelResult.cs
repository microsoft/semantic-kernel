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
    public async Task GetTokenUsageMetadata()
    {
        this._output.WriteLine("======== Inline Function Definition + Invocation ========");

        // Create kernel
        Kernel kernel = Kernel.CreateBuilder()
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
        this._output.WriteLine(result.GetValue<string>());
        this._output.WriteLine(result.Metadata?["Usage"]?.AsJson());
        this._output.WriteLine();
    }

    public Example43_GetModelResult(ITestOutputHelper output) : base(output)
    {
    }
}
