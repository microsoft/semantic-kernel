// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Core;

/// <summary>
/// Integration tests for <see cref="ChatReducerTriggerEvent.AfterToolCallResponseReceived"/>.
/// </summary>
public class AfterToolCallResponseReceivedTests
{
    /// <summary>
    /// Verify that the AfterToolCallResponseReceived trigger fires when function results are received.
    /// </summary>
    [Fact]
    public async Task VerifyAfterToolCallResponseReceivedTriggerFiresAsync()
    {
        // Arrange
        var reducer = new CountingReducer(ChatReducerTriggerEvent.AfterToolCallResponseReceived);
        var agent = new MockAgent { HistoryReducer = reducer };
        var history = new ChatHistory();

        history.AddUserMessage("User message 1");
        history.AddAssistantMessage("Assistant response 1");

        // Add a function call and result
        history.Add(new ChatMessageContent(AuthorRole.Assistant, [new FunctionCallContent("test-func")]));
        history.Add(new ChatMessageContent(AuthorRole.Tool, [new FunctionResultContent("test-func", "result")]));

        // Act - trigger reduction with the AfterToolCallResponseReceived event
        await agent.ReduceAsync(history, ChatReducerTriggerEvent.AfterToolCallResponseReceived);

        // Assert - the reducer should have been invoked
        Assert.Equal(1, reducer.InvocationCount);
    }

    /// <summary>
    /// Verify that the AfterToolCallResponseReceived trigger does not fire for non-tool messages.
    /// </summary>
    [Fact]
    public async Task VerifyAfterToolCallResponseReceivedTriggerDoesNotFireForNonToolMessagesAsync()
    {
        // Arrange
        var reducer = new CountingReducer(ChatReducerTriggerEvent.AfterToolCallResponseReceived);
        var agent = new MockAgent { HistoryReducer = reducer };
        var history = new ChatHistory();

        history.AddUserMessage("User message 1");
        history.AddAssistantMessage("Assistant response 1");

        // Act - trigger reduction with BeforeMessagesRetrieval (not the configured trigger)
        await agent.ReduceAsync(history, ChatReducerTriggerEvent.BeforeMessagesRetrieval);

        // Assert - the reducer should NOT have been invoked because it's only configured for AfterToolCallResponseReceived
        Assert.Equal(0, reducer.InvocationCount);
    }

    /// <summary>
    /// Verify that the reducer is invoked multiple times for multiple tool call responses.
    /// </summary>
    [Fact]
    public async Task VerifyMultipleToolCallResponsesInvokeReducerMultipleTimesAsync()
    {
        // Arrange
        var reducer = new CountingReducer(ChatReducerTriggerEvent.AfterToolCallResponseReceived);
        var agent = new MockAgent { HistoryReducer = reducer };
        var history = new ChatHistory();

        history.AddUserMessage("User message 1");

        // Add multiple function calls and results
        for (int i = 0; i < 3; i++)
        {
            history.Add(new ChatMessageContent(AuthorRole.Assistant, [new FunctionCallContent($"test-func-{i}")]));
            history.Add(new ChatMessageContent(AuthorRole.Tool, [new FunctionResultContent($"test-func-{i}", $"result-{i}")]));

            // Trigger reduction after each tool call response
            await agent.ReduceAsync(history, ChatReducerTriggerEvent.AfterToolCallResponseReceived);
        }

        // Assert - the reducer should have been invoked 3 times
        Assert.Equal(3, reducer.InvocationCount);
    }

    /// <summary>
    /// Test reducer that counts invocations.
    /// </summary>
    private sealed class CountingReducer : ChatHistoryReducerBase
    {
        public int InvocationCount { get; private set; }

        public CountingReducer(params ChatReducerTriggerEvent[] triggerEvents)
            : base(triggerEvents)
        {
        }

        public override Task<IEnumerable<ChatMessageContent>?> ReduceAsync(
            IReadOnlyList<ChatMessageContent> chatHistory,
            CancellationToken cancellationToken = default)
        {
            this.InvocationCount++;
            // Return null to indicate no reduction occurred (for testing purposes)
            return Task.FromResult<IEnumerable<ChatMessageContent>?>(null);
        }
    }
}
