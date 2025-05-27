// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Options for the <see cref="ContextualFunctionProvider"/>.
/// </summary>
[Experimental("SKEXP0130")]
public sealed class ContextualFunctionProviderOptions
{
    /// <summary>
    /// A callback function that returns a value used to create a context embedding. The value is vectorized,
    /// and the resulting vector is used to perform vector searches for functions relevant to the context.
    /// If not provided, the default behavior is to concatenate the non-empty messages into a single string,
    /// separated by a new line.
    /// </summary>
    public Func<ICollection<ChatMessage>, CancellationToken, Task<string>>? ContextEmbeddingValueProvider { get; set; }

    /// <summary>
    /// A callback function that returns a value used to create a function embedding. The value is vectorized,
    /// and the resulting vector is stored in the vector store for use in vector searches for functions relevant
    /// to the context.
    /// If not provided, the default behavior is to concatenate the function name and description into a single string.
    /// </summary>
    public Func<AIFunction, CancellationToken, Task<string>>? EmbeddingValueProvider { get; set; }
}
