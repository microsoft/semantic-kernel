// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Filters;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI;

/// <summary>
/// Unit testing of <see cref="AgentChatFilterInvokedContext"/>.
/// </summary>
public class AgentChatFilterInvokedContextTests
{
    /// <summary>
    /// Verify initial state.
    /// </summary>
    [Fact]
    public void VerifyAgentChatFilterInvokedContextState()
    {
        Mock<Agent> agent = new();
        ChatHistory history = [];
        ChatMessageContent message = new(AuthorRole.User, "hi");

        AgentChatFilterInvokedContext context = new(agent.Object, history, message);

        Assert.NotNull(context.Agent);
        Assert.NotNull(context.History);
        Assert.NotNull(context.Message);
    }
}
