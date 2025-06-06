// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadConformance;

public class OpenAIResponseAgentThreadTests() : AgentThreadTests(() => new OpenAIResponseAgentFixture())
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
