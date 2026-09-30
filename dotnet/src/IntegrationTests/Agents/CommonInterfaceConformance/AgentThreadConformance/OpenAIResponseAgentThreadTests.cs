// Copyright (c) Microsoft. All rights reserved.

// Temporarily disabled until the OpenAI API key and credits are restored.
#if false
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
#endif
