// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class BedrockAgentWithAIContextProviderTests() : AgentWithAIContextProviderTests<BedrockAgentFixture>(() => new BedrockAgentFixture())
{
    private const string ManualVerificationSkipReason = "This test is for manual verification.";

    [Fact(Skip = ManualVerificationSkipReason)]
    public override Task StatePartReceivesMessagesFromAgentAsync()
    {
        return base.StatePartReceivesMessagesFromAgentAsync();
    }

    [Fact(Skip = ManualVerificationSkipReason)]
    public override Task StatePartReceivesMessagesFromAgentWhenStreamingAsync()
    {
        return base.StatePartReceivesMessagesFromAgentWhenStreamingAsync();
    }

    [Fact(Skip = ManualVerificationSkipReason)]
    public override Task StatePartPreInvokeStateIsUsedByAgentAsync()
    {
        return base.StatePartPreInvokeStateIsUsedByAgentAsync();
    }

    [Fact(Skip = ManualVerificationSkipReason)]
    public override Task StatePartPreInvokeStateIsUsedByAgentWhenStreamingAsync()
    {
        return base.StatePartPreInvokeStateIsUsedByAgentWhenStreamingAsync();
    }
}
