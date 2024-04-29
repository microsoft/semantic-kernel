// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ChatCompletion;

// These examples show how to use a custom HttpClient with SK connectors.
public class Connectors_CustomHttpClient(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Demonstrates the usage of the default HttpClient provided by the SK SDK.
    /// </summary>
    [Fact]
    public void UseDefaultHttpClient()
    {
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey) // If you need to use the default HttpClient from the SK SDK, simply omit the argument for the httpMessageInvoker parameter.
            .Build();
    }

    /// <summary>
    /// Demonstrates the usage of a custom HttpClient.
    /// </summary>
    [Fact]
    public void UseCustomHttpClient()
    {
        using var httpClient = new HttpClient();

        // If you need to use a custom HttpClient, simply pass it as an argument for the httpClient parameter.
        var kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey,
                httpClient: httpClient)
            .Build();
    }
}
