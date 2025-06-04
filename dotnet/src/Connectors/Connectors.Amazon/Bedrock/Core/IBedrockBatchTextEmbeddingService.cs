// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Bedrock input-output service to build the request and response bodies as required by the given model.
/// <remarks>This service is used to embed multiple text strings in compatible models.</remarks>
/// <seealso cref="IBedrockCommonSplitTextEmbeddingGenerationService"/>
/// </summary>
internal interface IBedrockCommonBatchTextEmbeddingGenerationService : IBedrockCommonTextEmbeddingGenerationService
{
    /// <summary>
    /// Get the request body for the Invoke Model call.
    /// </summary>
    /// <param name="modelId">The model ID to use for the request.</param>
    /// <param name="texts">The list of texts to embed.</param>
    /// <returns>The request body for the Invoke Model call.</returns>
    internal object GetInvokeModelRequestBody(string modelId, IList<string> texts);

    /// <summary>
    /// Get the response body for the Invoke Model call.
    /// </summary>
    /// <param name="response"></param>
    /// <returns>The embedding from the response body.</returns>
    internal IList<ReadOnlyMemory<float>> GetInvokeResponseBody(InvokeModelResponse response);
}
