// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Exposes a Semantic Kernel <see cref="ChatCompletionAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
/// </summary>
public static class ChatCompletionAgentExtensions
{
    /// <summary>
    /// Exposes a Semantic Kernel Agent Framework <see cref="ChatCompletionAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
    /// </summary>
    /// <param name="chatCompletionAgent">The Semantic Kernel <see cref="ChatCompletionAgent"/> to expose as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.</param>
    /// <returns>The Semantic Kernel Agent Framework <see cref="Agent"/> exposed as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/></returns>
    [Experimental("SKEXP0110")]
    public static MAAI.AIAgent AsAIAgent(this ChatCompletionAgent chatCompletionAgent)
        => chatCompletionAgent.AsAIAgent(
            () => new ChatHistoryAgentThread(),
            (json, options) =>
            {
                var chatHistory = JsonSerializer.Deserialize<ChatHistory>(json);
                return chatHistory is null ? new ChatHistoryAgentThread() : new ChatHistoryAgentThread(chatHistory);
            },
            (thread, options) => JsonSerializer.SerializeToElement((thread as ChatHistoryAgentThread)?.ChatHistory));
}
