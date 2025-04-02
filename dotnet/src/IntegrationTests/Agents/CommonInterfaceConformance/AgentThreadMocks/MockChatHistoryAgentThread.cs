// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadMocks;

/// <summary>
/// Mock implementation of <see cref="ChatHistoryAgentThread"/> to allow
/// checking of messages received.
/// </summary>
public class MockChatHistoryAgentThread : ChatHistoryAgentThread, IMessageMockableAgentThread
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
