// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.SemanticKernelAIAgentConformance;

public class OpenAIResponseAgentAdapterTests() : SemanticKernelAIAgentTests(() => new OpenAIResponseAgentFixture())
{
    private const string TempOAIKeySkipReason = "Temporarily disabled until the OpenAI API key and credits are restored.";

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task ConvertAndRunAgentAsync()
    {
        return base.ConvertAndRunAgentAsync();
    }
}
