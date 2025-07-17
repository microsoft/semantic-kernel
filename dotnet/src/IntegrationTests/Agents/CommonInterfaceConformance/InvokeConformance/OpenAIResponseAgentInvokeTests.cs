// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeConformance;

public class OpenAIResponseAgentStoreEnabledInvokeTests() : InvokeTests(() => new OpenAIResponseAgentFixture(true))
{
    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} excludes the final response from the remote history.")]
    public override Task ConversationMaintainsHistoryAsync()
    {
        return base.ConversationMaintainsHistoryAsync();
    }

    /// <summary>
    /// <see cref="OpenAIResponseAgent"/> must be invoked with a message.
    /// </summary>
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

public class OpenAIResponseAgentStoreDisabledInvokeTests() : InvokeTests(() => new OpenAIResponseAgentFixture(false))
{
    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} excludes the final response from the remote history.")]
    public override Task ConversationMaintainsHistoryAsync()
    {
        return base.ConversationMaintainsHistoryAsync();
    }

    /// <summary>
    /// <see cref="OpenAIResponseAgent"/> must be invoked with a message.
    /// </summary>
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

    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} does not current support tool messages provided as input, causing local threads with tool calls to fail")]
    public override Task MultiStepInvokeWithPluginAndArgOverridesAsync()
    {
        return base.MultiStepInvokeWithPluginAndArgOverridesAsync();
    }
}
