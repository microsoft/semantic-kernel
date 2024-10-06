// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

/// <summary>
/// This example shows how to use GPT3.5 Chat model for prompts and prompt functions.
/// </summary>
public class Example27_PromptFunctionsUsingChatGPT : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        WriteLine("======== Using Chat GPT model for text generation ========");

        Kernel kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId)
            .Build();

        var func = kernel.CreateFunctionFromPrompt(
            "List the two planets closest to '{{$input}}', excluding moons, using bullet points.");

        var result = await func.InvokeAsync(kernel, new() { ["input"] = "Jupiter" });
        WriteLine(result.GetValue<string>());

        /*
        Output:
           - Saturn
           - Uranus
        */
    }

    public Example27_PromptFunctionsUsingChatGPT(ITestOutputHelper output) : base(output)
    {
    }
}
