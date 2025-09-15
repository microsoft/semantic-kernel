// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text.Json;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal class AmazonEmbedGenerationService : IBedrockCommonSplitTextEmbeddingGenerationService
{
    /// <inheritdoc />
    public object GetInvokeModelRequestBody(string modelId, string text)
    {
        return new TitanEmbedRequest()
        {
            InputText = text
        };
    }

    /// <inheritdoc />
    public ReadOnlyMemory<float> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<TitanTextEmbeddingResponse>(reader.ReadToEnd());
        if (responseBody?.Embedding is not { Length: > 0 })
        {
            return ReadOnlyMemory<float>.Empty;
        }

        return responseBody.Embedding;
    }
}
