// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadConformance;

public class ChatCompletionAgentThreadTests() : AgentThreadTests(() => new ChatCompletionAgentFixture())
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
