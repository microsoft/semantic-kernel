// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class OpenAIResponseAgentWithAIContextProviderTests() : AgentWithAIContextProviderTests<OpenAIResponseAgentFixture>(() => new OpenAIResponseAgentFixture())
{
    private const string TempOAIKeySkipReason = "Temporarily disabled until the OpenAI API key and credits are restored.";

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task StatePartReceivesMessagesFromAgentAsync()
    {
        return base.StatePartReceivesMessagesFromAgentAsync();
    }

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task StatePartReceivesMessagesFromAgentWhenStreamingAsync()
    {
        return base.StatePartReceivesMessagesFromAgentWhenStreamingAsync();
    }

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task StatePartPreInvokeStateIsUsedByAgentAsync()
    {
        return base.StatePartPreInvokeStateIsUsedByAgentAsync();
    }

    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task StatePartPreInvokeStateIsUsedByAgentWhenStreamingAsync()
    {
        return base.StatePartPreInvokeStateIsUsedByAgentWhenStreamingAsync();
    }
}
