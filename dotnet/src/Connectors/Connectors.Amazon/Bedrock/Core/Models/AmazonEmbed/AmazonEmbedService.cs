// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text.Json;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal class AmazonEmbedService : IBedrockTextEmbeddingService
{
    public object GetInvokeModelRequestBody(string modelId, string text, int dimensions = 1024, bool normalize = true)
    {
        return new TitanEmbedRequest()
        {
            InputText = text,
            Dimensions = dimensions,
            Normalize = normalize
        };
    }

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
