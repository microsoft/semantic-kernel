// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatWithAgent.Web;

/// <summary>
/// The agent completions API client.
/// </summary>
internal sealed class AgentCompletionsApiClient
{
    private readonly HttpClient _httpClient;
    private readonly ChatHistory _chatHistory;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentCompletionsApiClient"/> class.
    /// </summary>
    /// <param name="httpClient">The HTTP client.</param>
    public AgentCompletionsApiClient(HttpClient httpClient)
    {
        this._httpClient = httpClient;
        this._chatHistory = [];
    }

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
            ChatHistory = this._chatHistory,
            IsStreaming = true,
        };

        var result = await this._httpClient.PostAsJsonAsync<AgentCompletionRequest>("/agent/completions", request, cancellationToken).ConfigureAwait(false);

        result.EnsureSuccessStatusCode();

        var streamedContent = result.Content.ReadFromJsonAsAsyncEnumerable<StreamingChatMessageContent>(cancellationToken);

        StringBuilder builder = new();

        await foreach (StreamingChatMessageContent? update in streamedContent.ConfigureAwait(false))
        {
            if (string.IsNullOrEmpty(update?.Content))
            {
                continue;
            }

            builder.Append(update.Content);

            yield return update.Content;
        }

        // Keep original prompt and agent response to maintain chat history
        this._chatHistory.AddUserMessage(prompt);
        this._chatHistory.AddAssistantMessage(builder.ToString());
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
        /// Gets or sets the chat history.
        /// </summary>
        public required ChatHistory ChatHistory { get; set; }

        /// <summary>
        /// Gets or sets a value indicating whether streaming is requested.
        /// </summary>
        public bool IsStreaming { get; set; }
    }
}
