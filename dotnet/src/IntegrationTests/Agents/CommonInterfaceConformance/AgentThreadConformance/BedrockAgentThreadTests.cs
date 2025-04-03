// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadConformance;

public class BedrockAgentThreadTests() : AgentThreadTests(() => new BedrockAgentFixture())
{
    [Fact(Skip = "Manual verification only")]
    public override Task OnNewMessageWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        // The Bedrock agent does not support writing to a thread with OnNewMessage.
        return Task.CompletedTask;
    }

    [Fact(Skip = "Manual verification only")]
    public override Task DeletingThreadTwiceDoesNotThrowAsync()
    {
        return base.DeletingThreadTwiceDoesNotThrowAsync();
    }

    [Fact(Skip = "Manual verification only")]
    public override Task UsingThreadAfterDeleteThrowsAsync()
    {
        return base.UsingThreadAfterDeleteThrowsAsync();
    }

    [Fact(Skip = "Manual verification only")]
    public override Task DeleteThreadBeforeCreateThrowsAsync()
    {
        return base.DeleteThreadBeforeCreateThrowsAsync();
    }

    [Fact(Skip = "Manual verification only")]
    public override Task UsingThreadBeforeCreateCreatesAsync()
    {
        return base.UsingThreadBeforeCreateCreatesAsync();
    }

    [Fact(Skip = "Manual verification only")]
    public override Task DeleteThreadWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        return base.DeleteThreadWithServiceFailureThrowsAgentOperationExceptionAsync();
    }
}
