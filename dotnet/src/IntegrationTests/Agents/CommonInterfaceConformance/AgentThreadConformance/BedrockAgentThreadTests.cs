// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadConformance;

public class BedrockAgentThreadTests() : AgentThreadTests(() => new BedrockAgentFixture())
{
    [Fact(Skip = "This test is for manual verification.")]
    public override Task OnNewMessageWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        // The Bedrock agent does not support writing to a thread with OnNewMessage.
        return Task.CompletedTask;
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task DeletingThreadTwiceDoesNotThrowAsync()
    {
        return base.DeletingThreadTwiceDoesNotThrowAsync();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task UsingThreadAfterDeleteThrowsAsync()
    {
        return base.UsingThreadAfterDeleteThrowsAsync();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task DeleteThreadBeforeCreateThrowsAsync()
    {
        return base.DeleteThreadBeforeCreateThrowsAsync();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task UsingThreadBeforeCreateCreatesAsync()
    {
        return base.UsingThreadBeforeCreateCreatesAsync();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public override Task DeleteThreadWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        return base.DeleteThreadWithServiceFailureThrowsAgentOperationExceptionAsync();
    }
}
