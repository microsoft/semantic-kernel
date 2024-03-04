// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client;

/// <summary>
/// Represents the response from the Hugging Face text embedding API.
/// </summary>
internal sealed class TextEmbeddingResponse : List<List<List<ReadOnlyMemory<float>>>>
{
}
