#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;

internal interface IGeminiTokenCounterClient
{
    /// <summary>
    /// Counts the number of tokens asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt to count tokens from.</param>
    /// <param name="executionSettings">Optional settings for prompt execution.</param>
    /// <param name="cancellationToken">A cancellation token to cancel the operation.</param>
    /// <returns>The number of tokens.</returns>
    Task<int> CountTokensAsync(
        string prompt,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);
}
