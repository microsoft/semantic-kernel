// Copyright (c) Microsoft. All rights reserved.

using System;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Bedrock input-output service to build the request and response bodies as required by the given model.
/// <remarks>This service is used to embed a single text string at a time in models that can't handle batch inputs.</remarks>
/// <seealso cref="IBedrockCommonBatchTextEmbeddingGenerationService"/>
/// </summary>
internal interface IBedrockCommonSplitTextEmbeddingGenerationService : IBedrockCommonTextEmbeddingGenerationService
{
    /// <summary>
    /// Get the request body for the Invoke Model call.
    /// </summary>
    /// <param name="modelId">The model ID to use for the request.</param>
    /// <param name="text">The text to embed.</param>
    /// <returns>The request body for the Invoke Model call.</returns>
    internal object GetInvokeModelRequestBody(string modelId, string text);

    /// <summary>
    /// Get the response body for the Invoke Model call.
    /// </summary>
    /// <param name="response"></param>
    /// <returns>The embeddings from the response body.</returns>
    internal ReadOnlyMemory<float> GetInvokeResponseBody(InvokeModelResponse response);
}
