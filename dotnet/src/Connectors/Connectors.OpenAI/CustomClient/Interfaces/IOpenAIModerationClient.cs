// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Represents a client for interacting with the openai moderation models.
/// </summary>
internal interface IOpenAIModerationClient
{
    /// <summary>
    /// Classifies the given text using the openai moderation models.
    /// </summary>
    /// <param name="text">The text to classify.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>The result of the classification.</returns>
    public Task<ClassificationContent> ClassifyTextAsync(
        string text,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default);
}
