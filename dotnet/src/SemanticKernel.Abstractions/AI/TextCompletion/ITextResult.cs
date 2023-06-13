// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.AI.TextCompletion;

/// <summary>
/// Interface for text completion results
/// </summary>
public interface ITextResult
{
    /// <summary>
    /// Gets the model result data.
    /// </summary>
    ModelResult ModelResult { get; }

    Task<string> GetCompletionAsync(CancellationToken cancellationToken = default);
}
