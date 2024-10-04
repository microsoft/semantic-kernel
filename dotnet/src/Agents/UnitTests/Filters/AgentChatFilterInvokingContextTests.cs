// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Filters;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="AgentChatFilterInvokingContext"/>.
/// </summary>
public class AgentChatFilterInvokingContextTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void VerifyAgentChatFilterInvokingContextState()
    {
        Mock<Agent> agent = new();
        ChatHistory history = [];

        AgentChatFilterInvokingContext context = new(agent.Object, history);

        Assert.NotNull(context.Agent);
        Assert.NotNull(context.History);
    }
}
