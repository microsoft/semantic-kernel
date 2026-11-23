// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeStreamingConformance;

[Collection("Sequential")]
public class OpenAIResponseAgentInvokeStreamingTests() : InvokeStreamingTests(() => new OpenAIResponseAgentFixture())
{
    private const string TempOAIKeySkipReason = "Temporarily disabled until the OpenAI API key and credits are restored.";

    [RetryFact(3, 10_000, Skip = TempOAIKeySkipReason)]
    public override Task InvokeStreamingAsyncReturnsResultAsync()
    {
        return base.InvokeStreamingAsyncReturnsResultAsync();
    }

    [RetryFact(3, 10_000, Skip = TempOAIKeySkipReason)]
    public override Task InvokeStreamingAsyncWithoutThreadCreatesThreadAsync()
    {
        return base.InvokeStreamingAsyncWithoutThreadCreatesThreadAsync();
    }

    [RetryFact(3, 10_000, Skip = TempOAIKeySkipReason)]
    public override Task MultiStepInvokeStreamingAsyncWithPluginAndArgOverridesAsync()
    {
        return base.MultiStepInvokeStreamingAsyncWithPluginAndArgOverridesAsync();
    }

    [RetryFact(3, 10_000, Skip = TempOAIKeySkipReason)]
    public override Task InvokeStreamingWithPluginNotifiesForAllMessagesAsync()
    {
        return base.InvokeStreamingWithPluginNotifiesForAllMessagesAsync();
    }

    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} excludes the final response from the remote history.")]
    public override Task ConversationMaintainsHistoryAsync()
    {
        return base.ConversationMaintainsHistoryAsync();
    }

    /// <summary>
    /// <see cref="OpenAIResponseAgent"/> must be invoked with a message.
    /// </summary>
    [Fact(Skip = TempOAIKeySkipReason)]
    public override Task InvokeStreamingAsyncWithoutMessageCreatesThreadAsync()
    {
        return Assert.ThrowsAsync<ClientResultException>(() => base.InvokeStreamingAsyncWithoutMessageCreatesThreadAsync());
    }
}
