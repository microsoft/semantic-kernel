// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeConformance;

public class OpenAIResponseAgentInvokeTests() : InvokeTests(() => new OpenAIResponseAgentFixture())
{
    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} excludes the final response from the remote history.")]
    public override Task ConversationMaintainsHistoryAsync()
    {
        return base.ConversationMaintainsHistoryAsync();
    }

    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} fails to notify for all messages - Issue #12468")]
    public override Task InvokeWithPluginNotifiesForAllMessagesAsync()
    {
        return base.InvokeWithPluginNotifiesForAllMessagesAsync();
    }
}
