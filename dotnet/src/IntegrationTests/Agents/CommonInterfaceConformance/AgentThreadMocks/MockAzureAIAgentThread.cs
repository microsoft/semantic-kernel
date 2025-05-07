// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.Projects;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.AzureAI;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadMocks;

/// <summary>
/// Mock implementation of <see cref="AzureAIAgentThread"/> to allow
/// checking of messages received.
/// </summary>
public class MockAzureAIAgentThread(AgentsClient client, string id) : AzureAIAgentThread(client, id), IMessageMockableAgentThread
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
