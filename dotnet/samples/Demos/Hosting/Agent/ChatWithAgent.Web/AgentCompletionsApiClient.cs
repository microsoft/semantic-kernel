// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.SemanticKernel;

namespace ChatWithAgent.Web;

/// <summary>
/// The agent completions API client.
/// </summary>
/// <param name="httpClient">The HTTP client.</param>
internal sealed class AgentCompletionsApiClient(HttpClient httpClient)
{
    /// <summary>
    /// Completes the prompt asynchronously.
    /// </summary>
    /// <param name="prompt">The prompt.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The completion result.</returns>
    internal async IAsyncEnumerable<string> CompleteStreamingAsync(string prompt, [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var request = new AgentCompletionRequest()
        {
            Prompt = prompt,
            IsStreaming = true,
        };

        var result = await httpClient.PostAsJsonAsync<AgentCompletionRequest>("/agent/completions", request, cancellationToken).ConfigureAwait(false);

        result.EnsureSuccessStatusCode();

        var streamedContent = result.Content.ReadFromJsonAsAsyncEnumerable<StreamingChatMessageContent>(cancellationToken);

        await foreach (StreamingChatMessageContent? update in streamedContent.ConfigureAwait(false))
        {
            if (string.IsNullOrEmpty(update?.Content))
            {
                continue;
            }

            yield return update.Content;
        }
    }

    /// <summary>
    /// The agent completion request model.
    /// </summary>
    private sealed class AgentCompletionRequest
    {
        /// <summary>
        /// Gets or sets the prompt.
        /// </summary>
        public required string Prompt { get; set; }

        /// <summary>
        /// Gets or sets a value indicating whether streaming is requested.
        /// </summary>
        public bool IsStreaming { get; set; }
    }
}
