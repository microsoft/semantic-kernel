// Copyright (c) Microsoft. All rights reserved.

using System;
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

        Assert.NotNull(result1.Message);
        Assert.NotNull(result2.Message);

        // The Bedrock Agent returns empty results about half the time. Until this is fixed we cannot assert on the content so we only assert that the message is not null.
        // Additionally, the BedrockAgentThread cannot read messages from the thread so we cannot verify the history directly. This is a limitation of Bedrock Sessions.
        //Assert.Contains("Paris", result1.Message.Content);
        //Assert.Contains("Eiffel", result2.Message.Content);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override async Task InvokeReturnsResultAsync()
    {
        var agent = this.Fixture.Agent;
        var asyncResults = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "What is the capital of France."), this.Fixture.AgentThread);
        var results = await asyncResults.ToListAsync();
        Assert.Single(results);

        var firstResult = results.First();
        Assert.NotNull(firstResult.Thread);
        Assert.NotNull(firstResult.Message);

        // The Bedrock Agent returns empty results about half the time. Until this is fixed we cannot assert on the content so we only assert that the message is not null.
        //Assert.Contains("Paris", firstResult.Message.Content);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override async Task InvokeWithoutThreadCreatesThreadAsync()
    {
        var agent = this.Fixture.Agent;
        var asyncResults = agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, "What is the capital of France."));
        var results = await asyncResults.ToListAsync();
        Assert.Single(results);

        var firstResult = results.First();
        Assert.NotNull(firstResult.Message);
        Assert.NotNull(firstResult.Thread);

        // The Bedrock Agent returns empty results about half the time. Until this is fixed we cannot assert on the content so we only assert that the message is not null.
        //Assert.Contains("Paris", firstResult.Message.Content);

        await this.Fixture.DeleteThread(firstResult.Thread);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task InvokeWithoutMessageCreatesThreadAsync()
    {
        // The Bedrock agent does not support invoking without a message.
        return Assert.ThrowsAsync<InvalidOperationException>(async () => await base.InvokeWithoutThreadCreatesThreadAsync());
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task MultiStepInvokeWithPluginAndArgOverridesAsync()
    {
        return base.MultiStepInvokeWithPluginAndArgOverridesAsync();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task InvokeWithPluginNotifiesForAllMessagesAsync()
    {
        return base.InvokeWithPluginNotifiesForAllMessagesAsync();
    }
}
