// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal class CohereEmbedGenerationService : IBedrockCommonBatchTextEmbeddingGenerationService
{
    ///<inheritdoc />
    public object GetInvokeModelRequestBody(string modelId, IList<string> texts)
    {
        return new EmbedRequest
        {
            Texts = texts,
            InputType = "search_document"
        };
    }

    ///<inheritdoc />
    public IList<ReadOnlyMemory<float>> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<EmbedResponse>(reader.ReadToEnd());
        if (responseBody?.Embeddings is not { Count: > 0 })
        {
            return [ReadOnlyMemory<float>.Empty];
        }

        return responseBody.Embeddings.Select(item => new ReadOnlyMemory<float>([.. item!])).ToList();
    }
}
