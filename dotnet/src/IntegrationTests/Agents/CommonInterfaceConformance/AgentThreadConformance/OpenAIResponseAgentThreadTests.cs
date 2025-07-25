// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadConformance;

public class OpenAIResponseAgentStoreEnabledThreadTests() : AgentThreadTests(() => new OpenAIResponseAgentFixture(true))
{
    [Fact]
    public override Task OnNewMessageWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        // Test not applicable since we cannot add a message to the thread we can only respond to a message.
        return Task.CompletedTask;
    }

    [Fact]
    public override Task UsingThreadBeforeCreateCreatesAsync()
    {
        // Test not applicable since we cannot create a thread we can only respond to a message.
        return Task.CompletedTask;
    }
}

public class OpenAIResponseAgentStoreDisabledThreadTests() : AgentThreadTests(() => new OpenAIResponseAgentFixture(false))
{
    [Fact]
    public override Task DeleteThreadWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        // Test not applicable since there is no service to fail.
        return Task.CompletedTask;
    }

    [Fact]
    public override Task OnNewMessageWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        // Test not applicable since there is no service to fail.
        return Task.CompletedTask;
    }
}
