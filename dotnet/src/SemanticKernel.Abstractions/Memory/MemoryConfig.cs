// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Configuration for memory-related operations.
/// </summary>
[Experimental("SKEXP0003")]
public sealed class MemoryConfig
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryConfig"/> class.
    /// </summary>
    /// <param name="collectionName">Collection to use.</param>
    /// <param name="limit">How many results to return.</param>
    /// <param name="minRelevanceScore">Minimum relevance score, from 0 to 1, where 1 means exact match.</param>
    public MemoryConfig(string collectionName, int limit = 1, double minRelevanceScore = 0.7)
    {
        this.CollectionName = collectionName;
        this.Limit = limit;
        this.MinRelevanceScore = minRelevanceScore;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryConfig"/> class.
    /// </summary>
    /// <param name="memory">Instance of <see cref="ISemanticTextMemory"/> to call memory provider.</param>
    /// <param name="collectionName">Collection to use.</param>
    /// <param name="limit">How many results to return.</param>
    /// <param name="minRelevanceScore">Minimum relevance score, from 0 to 1, where 1 means exact match.</param>
    public MemoryConfig(ISemanticTextMemory memory, string collectionName, int limit = 1, double minRelevanceScore = 0.7)
        : this(collectionName, limit, minRelevanceScore)
    {
        this.Memory = memory;
    }

    /// <summary>
    /// Instance of <see cref="ISemanticTextMemory"/> to call memory provider.
    /// </summary>
    public ISemanticTextMemory? Memory { get; set; }

    /// <summary>
    /// Collection to use.
    /// </summary>
    public string CollectionName { get; set; }

    /// <summary>
    /// How many results to return.
    /// </summary>
    public int Limit { get; set; }

    /// <summary>
    /// Minimum relevance score, from 0 to 1, where 1 means exact match.
    /// </summary>
    public double MinRelevanceScore { get; set; }
}
