// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeStreamingConformance;

[Collection("Sequential")]
public class OpenAIResponseAgentStoreEnabledInvokeStreamingTests() : InvokeStreamingTests(() => new OpenAIResponseAgentFixture(true))
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
    public override Task InvokeStreamingAsyncWithoutMessageCreatesThreadAsync()
    {
        return Assert.ThrowsAsync<ArgumentException>(() => base.InvokeStreamingAsyncWithoutMessageCreatesThreadAsync());
    }
}

[Collection("Sequential")]
public class OpenAIResponseAgentStoreDisabledInvokeStreamingTests() : InvokeStreamingTests(() => new OpenAIResponseAgentFixture(false))
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
    public override Task InvokeStreamingAsyncWithoutMessageCreatesThreadAsync()
    {
        return Assert.ThrowsAsync<ArgumentException>(() => base.InvokeStreamingAsyncWithoutMessageCreatesThreadAsync());
    }

    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} does not current support tool messages provided as input, causing local threads with tool calls to fail")]
    public override Task MultiStepInvokeStreamingAsyncWithPluginAndArgOverridesAsync()
    {
        return base.MultiStepInvokeStreamingAsyncWithPluginAndArgOverridesAsync();
    }
}
