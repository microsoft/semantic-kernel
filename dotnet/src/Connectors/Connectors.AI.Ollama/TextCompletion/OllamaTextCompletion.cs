// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.Ollama.TextCompletion;

/// <summary>
/// Ollama text completion service.
/// </summary>
public sealed class OllamaTextCompletion : ITextCompletion
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OllamaTextCompletion"/> class.
    /// Using default <see cref="HttpClientHandler"/> implementation.
    /// </summary>
    /// <param name="endpoint">Endpoint for service API call.</param>
    /// <param name="model">Model to use for service API call.</param>
    public OllamaTextCompletion(Uri endpoint, string model)
    {
        Verify.NotNull(endpoint);
        Verify.NotNullOrWhiteSpace(model);
    }

    /// <inheritdoc/>
    [Obsolete("Streaming capability is not supported, use GetCompletionsAsync instead")]
    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(
        string text,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        throw new NotSupportedException("Streaming capability is not supported");
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(
        string text,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        throw new NotSupportedException("Completion capability is not supported");
    }

    #region private ================================================================================

    #endregion
}
