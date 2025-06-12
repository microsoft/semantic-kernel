// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.AgentWithStatePartConformance;

public class OpenAIResponseAgentWithAIContextProviderTests() : AgentWithAIContextProviderTests<OpenAIResponseAgentFixture>(() => new OpenAIResponseAgentFixture())
{
    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} fails to recieve context messages - Issue #12469")]
    public override Task StatePartReceivesMessagesFromAgentWhenStreamingAsync()
    {
        return base.StatePartReceivesMessagesFromAgentWhenStreamingAsync();
    }
}
