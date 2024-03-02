// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Extension methods for the <see cref="KernelAgent"/> class.
/// </summary>
public static class KernelAgentExtensions
{
    /// <summary>
    /// Invokes the agent to process the given messages and generate a response as a stream.
    /// </summary>
    /// <param name="agent">The agent to invoke.</param>
    /// <param name="messages">A list of the messages for the agent to process.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to cancel the operation.</param>
    /// <returns>List of messages representing the agent's response.</returns>
    /// <returns>Streaming list of content updates representing the agent's response.</returns>
    public static async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        this KernelAgent agent,
        IAsyncEnumerable<StreamingChatMessageContent> messages,
        PromptExecutionSettings? executionSettings = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var messagesPerChoice = new Dictionary<int, (AuthorRole? Role, string? Content, string? ModelId, IReadOnlyDictionary<string, object?>? Metadata)>();

        // For each chat completion update
        await foreach (StreamingChatMessageContent chatUpdate in messages)
        {
            if (!messagesPerChoice.TryGetValue(chatUpdate.ChoiceIndex, out var message))
            {
                message = new();
            }

            if (chatUpdate.Role is not null)
            {
                message.Role = chatUpdate.Role;
            }

            if (chatUpdate.Content is { Length: > 0 })
            {
                message.Content += chatUpdate.Content;
            }

            if (chatUpdate.ModelId is { Length: > 0 })
            {
                message.ModelId = chatUpdate.ModelId;
            }

            if (chatUpdate.Metadata is { Count: > 0 })
            {
                message.Metadata = chatUpdate.Metadata;
            }

            messagesPerChoice[chatUpdate.ChoiceIndex] = message;
        }

        var chat = new ChatHistory();

        foreach (var message in messagesPerChoice.Values)
        {
            chat.Add(new ChatMessageContent(
                role: message.Role ?? AuthorRole.User,
                content: message.Content?.ToString(),
                modelId: message.ModelId,
                metadata: message.Metadata
            ));
        }

        var response = agent.InvokeStreamingAsync(chat, executionSettings, cancellationToken).ConfigureAwait(false);

        await foreach (var message in response)
        {
            yield return message;
        }
    }
}
