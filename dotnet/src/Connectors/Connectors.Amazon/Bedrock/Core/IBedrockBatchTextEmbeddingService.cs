// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Bedrock input-output service to build the request and response bodies as required by the given model.
/// </summary>
internal interface IBedrockCommonBatchTextEmbeddingService : IBedrockCommonTextEmbeddingService
{
    internal object GetInvokeModelRequestBody(string modelId, IList<string> texts);

    internal IList<ReadOnlyMemory<float>> GetInvokeResponseBody(InvokeModelResponse response);
}
