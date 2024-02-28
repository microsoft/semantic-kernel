// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace;

/// <summary>
/// Represents the response from the Hugging Face text embedding API.
/// </summary>
public sealed class TextEmbeddingResponse : List<List<List<ReadOnlyMemory<float>>>>
{
}
