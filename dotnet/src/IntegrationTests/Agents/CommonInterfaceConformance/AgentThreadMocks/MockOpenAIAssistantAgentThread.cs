// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI.Assistants;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadMocks;

/// <summary>
/// Mock implementation of <see cref="OpenAIAssistantAgentThread"/> to allow
/// checking of messages received.
/// </summary>
public class MockOpenAIAssistantAgentThread(AssistantClient client, string id) : OpenAIAssistantAgentThread(client, id), IMessageMockableAgentThread
{
    protected override Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
        this.MockableOnNewMessage(newMessage, cancellationToken);
        return base.OnNewMessageInternalAsync(newMessage, cancellationToken);
    }

    public virtual void MockableOnNewMessage(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
    {
    }
}
