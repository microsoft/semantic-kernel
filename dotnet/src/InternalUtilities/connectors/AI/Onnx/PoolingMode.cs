// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Onnx;

/// <summary>Pooling mode used for creating the final sentence embedding.</summary>
public enum EmbeddingPoolingMode
{
    /// <summary>Uses the maximum across all token embeddings.</summary>
    Max,
    /// <summary>Calculates the average across all token embeddings.</summary>
    Mean,
    /// <summary>Calculates the average across all token embeddings, divided by the square root of the number of tokens.</summary>
    MeanSquareRootTokensLength,
}
