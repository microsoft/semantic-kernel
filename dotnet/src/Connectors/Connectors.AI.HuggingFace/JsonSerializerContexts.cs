// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextEmbedding;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(List<TextCompletionResponse>))]
[JsonSerializable(typeof(TextCompletionRequest))]
[JsonSerializable(typeof(TextEmbeddingRequest))]
[JsonSerializable(typeof(TextEmbeddingResponse))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
}
