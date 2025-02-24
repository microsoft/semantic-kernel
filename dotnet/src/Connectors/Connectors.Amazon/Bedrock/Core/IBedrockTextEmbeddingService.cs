// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Bedrock input-output service to build the request and response bodies as required by the given model.
/// </summary>
internal interface IBedrockTextEmbeddingService
{
    internal object GetInvokeModelRequestBody(string modelId, string text, int dimensions = 1024, bool normalize = true);

    internal ReadOnlyMemory<float> GetInvokeResponseBody(InvokeModelResponse response);
}
