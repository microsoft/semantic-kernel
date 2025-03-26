// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance;

/// <summary>
/// Base class for setting up and tearing down agents, to be used in tests.
/// Each agent type should have its own derived class.
/// </summary>
public abstract class AgentFixture : IAsyncLifetime
{
    public abstract Agent Agent { get; }

    public abstract AgentThread AgentThread { get; }

    public abstract AgentThread CreatedAgentThread { get; }

    public abstract AgentThread ServiceFailingAgentThread { get; }

    public abstract AgentThread CreatedServiceFailingAgentThread { get; }

    public abstract Task<ChatHistory> GetChatHistory();

    public abstract Task DeleteThread(AgentThread thread);

    public abstract Task DisposeAsync();

    public abstract Task InitializeAsync();
}
