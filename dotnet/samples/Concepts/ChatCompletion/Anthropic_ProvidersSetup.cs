// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace ChatCompletion;

/// <summary>
/// This sample shows how to setup different providers for anthropic.
/// </summary>
public sealed class Anthropic_ProvidersSetup(ITestOutputHelper output) : BaseTest(output)
{
    public void AnthropicProvider()
    {
        var kernel = Kernel.CreateBuilder()
            .AddAnthropicChatCompletion(
                modelId: "modelId",
                apiKey: "apiKey")
            .Build();
    }

    /// <summary>
    /// For more information on how to setup the Vertex AI provider, go to <see cref="Google_GeminiChatCompletion"/> sample.
    /// </summary>
    public void VertexAiProvider()
    {
        var kernel = Kernel.CreateBuilder()
            .AddAnthropicVertextAIChatCompletion(
                modelId: "modelId",
                bearerTokenProvider: () => ValueTask.FromResult("bearer"),
                endpoint: new Uri("https://your-endpoint"))
            .Build();
    }
}
