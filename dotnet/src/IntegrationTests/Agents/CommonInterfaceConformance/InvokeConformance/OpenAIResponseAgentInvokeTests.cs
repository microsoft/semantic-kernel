// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeConformance;

public class OpenAIResponseAgentInvokeTests() : InvokeTests(() => new OpenAIResponseAgentFixture())
{
    private const string TempOAIKeySkipReason = "Temporarily disabled until the OpenAI API key and credits are restored.";

    [RetryFact(3, 5000, Skip = TempOAIKeySkipReason)]
    public override Task InvokeReturnsResultAsync()
    {
        return base.InvokeReturnsResultAsync();
    }

    [RetryFact(3, 5000, Skip = TempOAIKeySkipReason)]
    public override Task InvokeWithoutThreadCreatesThreadAsync()
    {
        return base.InvokeWithoutThreadCreatesThreadAsync();
    }

    [RetryFact(3, 5000, Skip = TempOAIKeySkipReason)]
    public override Task MultiStepInvokeWithPluginAndArgOverridesAsync()
    {
        return base.MultiStepInvokeWithPluginAndArgOverridesAsync();
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
    public override Task InvokeWithoutMessageCreatesThreadAsync()
    {
        return Assert.ThrowsAsync<ClientResultException>(() => base.InvokeWithoutMessageCreatesThreadAsync());
    }

    [Fact(Skip = $"{nameof(OpenAIResponseAgent)} fails to notify for all messages - Issue #12468")]
    public override Task InvokeWithPluginNotifiesForAllMessagesAsync()
    {
        return base.InvokeWithPluginNotifiesForAllMessagesAsync();
    }
}
