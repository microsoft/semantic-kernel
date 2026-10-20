// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadConformance;

public class OpenAIResponseAgentThreadTests() : AgentThreadTests(() => new OpenAIResponseAgentFixture())
{
    private const string TempOAIKeySkipReason = "Temporarily disabled until the OpenAI API key and credits are restored.";

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task OnNewMessageWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        // Test not applicable since we cannot add a message to the thread we can only respond to a message.
        return Task.CompletedTask;
    }

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task UsingThreadBeforeCreateCreatesAsync()
    {
        // Test not applicable since we cannot create a thread we can only respond to a message.
        return Task.CompletedTask;
    }

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task DeletingThreadTwiceDoesNotThrowAsync()
    {
        return base.DeletingThreadTwiceDoesNotThrowAsync();
    }

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task UsingThreadAfterDeleteThrowsAsync()
    {
        return base.UsingThreadAfterDeleteThrowsAsync();
    }

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task DeleteThreadBeforeCreateThrowsAsync()
    {
        return base.DeleteThreadBeforeCreateThrowsAsync();
    }

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task DeleteThreadWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        return base.DeleteThreadWithServiceFailureThrowsAgentOperationExceptionAsync();
    }
}
