// Copyright (c) Microsoft. All rights reserved.

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
    internal async Task<string> CompleteAsync(string prompt, CancellationToken cancellationToken)
    {
        var result = await httpClient.PostAsJsonAsync<AgentCompletionRequest>("/agent/completions", new AgentCompletionRequest() { Prompt = prompt }, cancellationToken).ConfigureAwait(false);

        result.EnsureSuccessStatusCode();

        return await result.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
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
