// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentThreadConformance;

public class BedrockAgentThreadTests() : AgentThreadTests(() => new BedrockAgentFixture())
{
    [Fact]
    public override Task OnNewMessageWithServiceFailureThrowsAgentOperationExceptionAsync()
    {
        // The Bedrock agent does not support writing to a thread with OnNewMessage.
        return Task.CompletedTask;
    }
}
