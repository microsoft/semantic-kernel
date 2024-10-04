// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
<<<<<<< HEAD
<<<<<<< main
=======
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> ms/feature-error-handling
=======
>>>>>>> ce2496df6e0c39a7c9c1a70b1e013e81a7b8d9b9
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
        WriteLine(result.GetValue<string>());
        WriteLine(result.Metadata?["Usage"]?.AsJson());
        WriteLine();
    }

<<<<<<< HEAD
<<<<<<< main
    public Example43_GetModelResult(ITestOutputHelper output) : base(output)
    {
=======
        string OutputExceptionDetail(Exception? exception)
        {
            return exception switch
            {
                HttpOperationException httpException => new { StatusCode = httpException.StatusCode.ToString(), httpException.Message, httpException.ResponseContent }.AsJson(),
                { } e => new { e.Message }.AsJson(),
                _ => string.Empty
            };
        }
>>>>>>> ms/feature-error-handling
=======
    public Example43_GetModelResult(ITestOutputHelper output) : base(output)
    {
>>>>>>> ce2496df6e0c39a7c9c1a70b1e013e81a7b8d9b9
    }
}
