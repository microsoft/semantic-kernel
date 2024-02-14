// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

internal sealed class OllamaEndpointProvider : IEndpointProvider
{
    /// <summary>
    /// Initializes a new instance of the Ollama Endpoints class with the specified API key.
    /// </summary>
    /// <param name="baseUri">Base url for Ollama API</param>
    public OllamaEndpointProvider(Uri baseUri)
    {
        this.TextGenerationEndpoint = new Uri($"{baseUri}/api/generate");
        this.ChatCompletionEndpoint = new Uri($"{baseUri}/api/chat");
        this.StreamChatCompletionEndpoint = new Uri($"{baseUri}/api/chat");
        this.StreamTextGenerationEndpoint = new Uri($"{baseUri}/api/generate");
    }

    public Uri TextGenerationEndpoint { get; }
    public Uri StreamTextGenerationEndpoint { get; }
    public Uri ChatCompletionEndpoint { get; }
    public Uri StreamChatCompletionEndpoint { get; }
}
