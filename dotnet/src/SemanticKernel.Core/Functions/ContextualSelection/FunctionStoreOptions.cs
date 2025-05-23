// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Options for the <see cref="FunctionStore"/>
/// </summary>
internal sealed class FunctionStoreOptions
{
    /// <summary>
    /// The maximum number of relevant functions to retrieve from the vector store.
    /// </summary>
    public int MaxNumberOfFunctions { get; set; } = 5;

    /// <summary>
    /// The minimum relevance score for functions to be considered relevant.
    /// </summary>
    public double? MinimumRelevanceScore { get; set; }

    /// <summary>
    /// A callback function that returns a value used to create a function embedding. The value is vectorized,
    /// and the resulting vector is stored in the vector store for use in vector searches for functions relevant
    /// to the context.
    /// If not provided, the default behavior is to concatenate the function name and description into a single string.
    /// </summary>
    public Func<AIFunction, CancellationToken, Task<string>>? FunctionEmbeddingValueProvider { get; set; }
}
