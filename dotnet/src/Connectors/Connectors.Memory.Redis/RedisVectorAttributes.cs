// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Redis;
public enum VectorIndexAlgorithms
{
    HNSW,
    FLAT,
}

#pragma warning disable CA1720
public enum VectorTypes
{
    FLOAT32, FLOAT64
}

public enum VectorDistanceMetrics
{
    L2, IP, COSINE
}
