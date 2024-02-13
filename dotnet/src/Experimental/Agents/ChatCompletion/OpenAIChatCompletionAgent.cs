// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represent an agent that is built around the OpenAI ChatCompletion API.
/// </summary>
public class OpenAIChatCompletionAgent : ChatCompletionAgent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatCompletionAgent"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="instructions">The instructions for the agent.</param>
    /// <param name="executionSettings">The optional execution settings for the agent. If not provided, default settings will be used.</param>
    public OpenAIChatCompletionAgent(Kernel kernel, string instructions, OpenAIPromptExecutionSettings? executionSettings = null) : base(kernel, instructions, executionSettings)
    {
    }

    /// <inheritdoc/>
    protected override ChatMessageContent CreateChatMessage(AgentMessage message)
    {
        Verify.NotNull(message, nameof(message));

        if (message.Items is not { Count: > 0 })
        {
            throw new KernelException("Agent message has no content.");
        }

        if (message.Role == AuthorRole.User)
        {
            return new ChatMessageContent(role: message.Role, items: new(message.Items), innerContent: message);
        }

        if (message.Role == AuthorRole.Assistant)
        {
            if (message.Items.Count != 1)
            {
                throw new KernelException("Agent message can't have more than one piece of content for the assistant role.");
            }

            var content = message.Items.Single();

            if (content is TextContent textContent)
            {
                return new ChatMessageContent(
                    role: message.Role,
                    content: textContent.Text,
                    encoding: textContent.Encoding,
                    metadata: textContent.Metadata,
                    innerContent: message);
            }

            throw new KernelException($"Agent message has an unsupported content type '{content.GetType()}' for the assistant role.");
        }

        return new ChatMessageContent(role: message.Role, items: new(message.Items), innerContent: message);
    }

    /// <inheritdoc/>
    protected override AgentMessage CreateAgentMessage(ChatMessageContent message)
    {
        Verify.NotNull(message, nameof(message));

        return new AgentMessage(
            role: message.Role,
            content: message.Content,
            innerMessage: message,
            agent: this);
    }
}
