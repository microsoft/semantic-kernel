// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

internal sealed class OllamaEndpointProvider : IEndpointProvider
{
    /// <summary>
    /// Initializes a new instance of the Ollama Endpoints class with the specified API key.
    /// </summary>
    /// <param name="baseUrl">Base url for Ollama API</param>
    public OllamaEndpointProvider(string baseUrl)
    {
        this.TextGenerationEndpoint = new Uri($"{baseUrl}/api/generate");
        this.ChatCompletionEndpoint = new Uri($"{baseUrl}/api/chat");
        this.StreamChatCompletionEndpoint= new Uri($"{baseUrl}/api/chat");
        this.StreamTextGenerationEndpoint= new Uri($"{baseUrl}/api/generate");
    }
    public Uri TextGenerationEndpoint { get; }
    public Uri StreamTextGenerationEndpoint { get; }
    public Uri ChatCompletionEndpoint { get; }
    public Uri StreamChatCompletionEndpoint { get; }
}
