// Copyright (c) Microsoft. All rights reserved.

using System;
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

    /// <remarks>
    /// <see cref="OpenAIResponseAgent"/> must be invoked with a message.
    /// </remarks>
    [Fact]
    public override Task InvokeWithoutMessageCreatesThreadAsync()
    {
        return Assert.ThrowsAsync<ArgumentException>(() => base.InvokeWithoutMessageCreatesThreadAsync());
    }

    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} fails to notify for all messages - Issue #12468")]
    public override Task InvokeWithPluginNotifiesForAllMessagesAsync()
    {
        return base.InvokeWithPluginNotifiesForAllMessagesAsync();
    }
}
