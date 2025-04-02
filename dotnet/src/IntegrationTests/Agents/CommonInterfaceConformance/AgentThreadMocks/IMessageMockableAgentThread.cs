// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadMocks;

/// <summary>
/// Interface for mocking <see cref="AgentThread"/> objects in a way that we can check messages sent to the thread.
/// </summary>
public interface IMessageMockableAgentThread
{
    void MockableOnNewMessage(ChatMessageContent newMessage, CancellationToken cancellationToken = default);
}
