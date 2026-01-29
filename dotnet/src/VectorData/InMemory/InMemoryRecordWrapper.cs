// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

internal readonly struct InMemoryRecordWrapper<TRecord>
{
    public InMemoryRecordWrapper(TRecord record)
    {
        this.Record = record;
    }

    [JsonConstructor]
    public InMemoryRecordWrapper(TRecord record, Dictionary<string, ReadOnlyMemory<float>> embeddingGeneratedVectors)
    {
        this.Record = record;
        this.EmbeddingGeneratedVectors = embeddingGeneratedVectors;
    }

    public TRecord Record { get; }
    public Dictionary<string, ReadOnlyMemory<float>> EmbeddingGeneratedVectors { get; } = [];
}
