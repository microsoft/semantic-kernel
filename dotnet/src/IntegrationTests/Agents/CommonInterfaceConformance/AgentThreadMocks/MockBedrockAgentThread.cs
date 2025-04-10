// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Amazon.BedrockAgentRuntime;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Bedrock;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadMocks;

/// <summary>
/// Mock implementation of <see cref="BedrockAgentThread"/> to allow
/// checking of messages received.
/// </summary>
public class MockBedrockAgentThread(AmazonBedrockAgentRuntimeClient client, string id) : BedrockAgentThread(client, id), IMessageMockableAgentThread
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
