// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Embeddings;

/// <summary>
/// Represents a generator of text embeddings of type <c>float</c>.
/// </summary>
[Experimental("SKEXP0001")]
public interface ITextEmbeddingGeneration : IEmbeddingGeneration<string, float>
{
}
