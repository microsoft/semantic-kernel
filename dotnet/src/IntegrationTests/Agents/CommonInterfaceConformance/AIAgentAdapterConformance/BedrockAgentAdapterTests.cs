// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AIAgentAdapterConformance;

public class BedrockAgentAdapterTests() : AIAgentAdapterTests(() => new BedrockAgentFixture())
{
    private const string ManualVerificationSkipReason = "This test is for manual verification.";

    [Fact(Skip = ManualVerificationSkipReason)]
    public override Task ConvertAndRunAgentAsync()
    {
        return base.ConvertAndRunAgentAsync();
    }
}
