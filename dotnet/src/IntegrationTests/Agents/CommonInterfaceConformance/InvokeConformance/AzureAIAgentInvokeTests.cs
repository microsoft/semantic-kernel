// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeConformance;

public class AzureAIAgentInvokeTests() : InvokeTests(() => new AzureAIAgentFixture())
{
    [Fact]
    public override Task InvokeWithPluginAndManualInvokeAsync()
    {
        // Manual invocation is not currently supported with the Azure AI Agent.
        return Task.CompletedTask;
    }
}
