// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Embeddings;

/// <summary>
/// Represents a generator of image embeddings of type <c>float</c>.
/// </summary>
[Experimental("SKEXP0001")]
public interface IImageEmbeddingGenerationService : IGenericEmbeddingGenerationService<ImageContent, float> { }
