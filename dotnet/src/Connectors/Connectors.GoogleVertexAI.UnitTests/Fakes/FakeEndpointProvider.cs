// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests;

public sealed class FakeEndpointProvider : IEndpointProvider
{
    public Uri GetGeminiTextGenerationEndpoint(string modelId)
        => new($"https://text-generation-endpoint.com/{modelId}/text-generation/");

    public Uri GetGeminiStreamTextGenerationEndpoint(string modelId)
        => new($"https://text-generation-endpoint.com/{modelId}/stream-text-generation/");

    public Uri GetGeminiChatCompletionEndpoint(string modelId)
        => new($"https://text-generation-endpoint.com/{modelId}/chat-completion/");

    public Uri GetGeminiStreamChatCompletionEndpoint(string modelId)
        => new($"https://text-generation-endpoint.com/{modelId}/stream-chat-completion/");

    public Uri GetEmbeddingsEndpoint(string modelId)
        => new($"https://text-generation-endpoint.com/{modelId}/embeddings/");

    public Uri GetCountTokensEndpoint(string modelId)
        => new($"https://text-generation-endpoint.com/{modelId}/count-tokens/");
}
