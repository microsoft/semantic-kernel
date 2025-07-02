// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeStreamingConformance;

[Collection("Sequential")]
public class OpenAIResponseAgentInvokeStreamingTests() : InvokeStreamingTests(() => new OpenAIResponseAgentFixture())
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
