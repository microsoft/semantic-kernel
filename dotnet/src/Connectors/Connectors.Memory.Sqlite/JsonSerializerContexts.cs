// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(Embedding<float>))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
}
