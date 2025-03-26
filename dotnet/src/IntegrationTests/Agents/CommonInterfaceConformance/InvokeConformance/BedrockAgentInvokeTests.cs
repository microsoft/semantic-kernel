// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeConformance;

public class BedrockAgentInvokeTests() : InvokeTests(() => new BedrockAgentFixture())
{
    [Fact(Skip = "This test is for manual verification.")]
    public override async Task ConversationMaintainsHistoryAsync()
    {
        var q1 = "What is the capital of France.";
        var q2 = "What is the tallest building in that city?";

        var agent = this.Fixture.Agent;
        var asyncResults1 = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, q1), this.Fixture.AgentThread);
        var result1 = await asyncResults1.FirstAsync();
        var asyncResults2 = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, q2), result1.Thread);
        var result2 = await asyncResults2.FirstAsync();

        Assert.Contains("Paris", result1.Message.Content);
        Assert.Contains("Eiffel", result2.Message.Content);

        // The BedrockAgentThread cannot read messages from the thread. This is a limitation of Bedrock Sessions.
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task InvokeReturnsResultAsync()
    {
        return base.InvokeReturnsResultAsync();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task InvokeWithoutThreadCreatesThreadAsync()
    {
        return base.InvokeWithoutThreadCreatesThreadAsync();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task MultiStepInvokeWithPluginAndArgOverridesAsync()
    {
        return base.MultiStepInvokeWithPluginAndArgOverridesAsync();
    }
}
