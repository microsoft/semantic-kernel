// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

internal readonly struct InMemoryVectorRecordWrapper<TRecord>(TRecord record)
{
    public TRecord Record { get; } = record;
    public Dictionary<string, ReadOnlyMemory<float>> EmbeddingGeneratedVectors { get; } = new();
}
