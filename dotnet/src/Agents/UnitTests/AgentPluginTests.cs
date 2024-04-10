// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests;

/// <summary>
/// Unit testing of <see cref="AgentPlugin"/>.
/// </summary>
public class AgentPluginTests
{
    /// <summary>
    /// Verify usage of <see cref="AgentPlugin"/>.
    /// </summary>
    [Fact]
    public async Task VerifyAgentPluginInvocationAsync()
    {
        KernelAgent agent = CreateMockAgent("a").Object;
        KernelPlugin plugin = agent.AsPlugin();

        Assert.Single(plugin);
        Assert.Equal(1, plugin.FunctionCount);
        Assert.False(plugin.TryGetFunction("missing", out KernelFunction? function));
        Assert.Null(function);
        Assert.True(plugin.TryGetFunction(plugin.Single().Name, out function));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(agent.Kernel, new() { { "input", "hi" } });
        IReadOnlyList<ChatMessageContent>? messages = result.GetValue<IReadOnlyList<ChatMessageContent>>();
        Assert.NotNull(messages);
        Assert.Single(messages);
    }

    private static Mock<ChatHistoryKernelAgent> CreateMockAgent(string response)
    {
        Mock<ChatHistoryKernelAgent> agent = new();

        ChatMessageContent[] messages = new[] { new ChatMessageContent(AuthorRole.Assistant, response) };
        agent.Setup(a => a.InvokeAsync(It.IsAny<IReadOnlyList<ChatMessageContent>>(), It.IsAny<CancellationToken>())).Returns(() => messages.ToAsyncEnumerable());

        return agent;
    }
}
