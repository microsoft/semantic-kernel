// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.SemanticKernelAIAgentConformance;

public class BedrockAgentAdapterTests() : SemanticKernelAIAgentTests(() => new BedrockAgentFixture())
{
    private const string ManualVerificationSkipReason = "This test is for manual verification.";

    [Fact(Skip = ManualVerificationSkipReason)]
    public override Task ConvertAndRunAgentAsync()
    {
        return base.ConvertAndRunAgentAsync();
    }
}
