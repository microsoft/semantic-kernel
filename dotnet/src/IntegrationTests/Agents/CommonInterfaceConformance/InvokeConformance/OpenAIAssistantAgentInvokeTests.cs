// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeConformance;

public class OpenAIAssistantAgentInvokeTests() : InvokeTests(() => new OpenAIAssistantAgentFixture())
{
    [Fact]
    public override Task InvokeWithPluginAndManualInvokeAsync()
    {
        // Manual invocation is not currently supported with the OpenAIAssistantAgent.
        return Task.CompletedTask;
    }
}
