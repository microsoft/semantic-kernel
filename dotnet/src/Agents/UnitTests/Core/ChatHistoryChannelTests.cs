// Copyright (c) Microsoft. All rights reserved.
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Unit testing of <see cref="ChatHistoryChannel"/>.
/// </summary>
public class ChatHistoryChannelTests
{
    /// <summary>
    /// Verify a <see cref="ChatHistoryChannel"/> throws if passed an agent that
    /// does not implement <see cref="IChatHistoryHandler"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentWithoutIChatHistoryHandlerAsync()
    {
        Mock<Agent> agent = new(); // Not a IChatHistoryHandler
        ChatHistoryChannel channel = new(); // Requires IChatHistoryHandler
        await Assert.ThrowsAsync<KernelException>(() => channel.InvokeAsync(agent.Object).ToArrayAsync().AsTask());
    }
}
