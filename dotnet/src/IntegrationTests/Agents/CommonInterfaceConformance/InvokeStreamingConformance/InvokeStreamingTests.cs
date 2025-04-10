// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeStreamingConformance;

/// <summary>
/// Base test class for testing the <see cref="Agent.InvokeStreamingAsync(ChatMessageContent, AgentThread?, AgentInvokeOptions?, System.Threading.CancellationToken)"/> method of agents.
/// Each agent type should have its own derived class.
/// </summary>
public abstract class InvokeStreamingTests(Func<AgentFixture> createAgentFixture) : IAsyncLifetime
{
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    private AgentFixture _agentFixture;
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.

    protected AgentFixture Fixture => this._agentFixture;

    [RetryFact(3, 10_000)]
    public virtual async Task InvokeStreamingAsyncReturnsResultAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;

        // Act
        var asyncResults = agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, "What is the capital of France."), this.Fixture.AgentThread);
        var results = await asyncResults.ToListAsync();

        // Assert
        var firstResult = results.First();
        var resultString = string.Join(string.Empty, results.Select(x => x.Message.Content));

        Assert.Contains("Paris", resultString);
        Assert.NotNull(firstResult.Thread);
    }

    [RetryFact(3, 10_000)]
    public virtual async Task InvokeStreamingAsyncWithoutThreadCreatesThreadAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;

        // Act
        var asyncResults = agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, "What is the capital of France."));
        var results = await asyncResults.ToListAsync();

        // Assert
        var firstResult = results.First();
        var resultString = string.Join(string.Empty, results.Select(x => x.Message.Content));

        Assert.Contains("Paris", resultString);
        Assert.NotNull(firstResult.Thread);

        // Cleanup
        await this.Fixture.DeleteThread(firstResult.Thread);
    }

    [RetryFact(3, 10_000)]
    public virtual async Task InvokeStreamingAsyncWithoutMessageCreatesThreadAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;

        // Act
        var asyncResults = agent.InvokeStreamingAsync();
        var results = await asyncResults.ToListAsync();

        // Assert
        var firstResult = results.First();
        var resultString = string.Join(string.Empty, results.Select(x => x.Message.Content));
        Assert.NotNull(firstResult.Thread);

        // Cleanup
        await this.Fixture.DeleteThread(firstResult.Thread);
    }

    [RetryFact(3, 10_000)]
    public virtual async Task ConversationMaintainsHistoryAsync()
    {
        // Arrange
        var q1 = "What is the capital of France.";
        var q2 = "What is the capital of Austria.";
        var agent = this.Fixture.Agent;

        // Act
        var asyncResults1 = agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, q1), this.Fixture.AgentThread);
        var results1 = await asyncResults1.ToListAsync();
        var resultString1 = string.Join(string.Empty, results1.Select(x => x.Message.Content));
        var result1 = results1.First();

        var asyncResults2 = agent.InvokeStreamingAsync(new ChatMessageContent(AuthorRole.User, q2), result1.Thread);
        var results2 = await asyncResults2.ToListAsync();
        var resultString2 = string.Join(string.Empty, results2.Select(x => x.Message.Content));

        // Assert
        Assert.Contains("Paris", resultString1);
        Assert.Contains("Austria", resultString2);

        var chatHistory = await this.Fixture.GetChatHistory();
        Assert.Equal(4, chatHistory.Count);
        Assert.Equal(2, chatHistory.Count(x => x.Role == AuthorRole.User));
        Assert.Equal(2, chatHistory.Count(x => x.Role == AuthorRole.Assistant));
        Assert.Equal(q1, chatHistory[0].Content);
        Assert.Equal(q2, chatHistory[2].Content);
        Assert.Contains("Paris", chatHistory[1].Content);
        Assert.Contains("Vienna", chatHistory[3].Content);
    }

    /// <summary>
    /// Verifies that the agent can invoke a plugin and respects the override
    /// Kernel and KernelArguments provided in the options.
    /// The step does multiple iterations to make sure that the agent
    /// also manages the chat history correctly.
    /// </summary>
    [RetryFact(3, 10_000)]
    public virtual async Task MultiStepInvokeStreamingAsyncWithPluginAndArgOverridesAsync()
    {
        // Arrange
        var questionsAndAnswers = new[]
        {
            ("Hello", string.Empty),
            ("What is the special soup?", "Clam Chowder"),
            ("What is the special drink?", "Chai Tea"),
            ("What is the special salad?", "Cobb Salad"),
            ("Thank you", string.Empty)
        };

        var agent = this.Fixture.Agent;
        var kernel = agent.Kernel.Clone();
        kernel.Plugins.AddFromType<MenuPlugin>();

        foreach (var questionAndAnswer in questionsAndAnswers)
        {
            // Act
            var asyncResults = agent.InvokeStreamingAsync(
                new ChatMessageContent(AuthorRole.User, questionAndAnswer.Item1),
                this.Fixture.AgentThread,
                options: new()
                {
                    Kernel = kernel,
                    KernelArguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() })
                });
            var results = await asyncResults.ToListAsync();

            // Assert
            var resultString = string.Join(string.Empty, results.Select(x => x.Message.Content));
            Assert.Contains(questionAndAnswer.Item2, resultString);
        }
    }

    /// <summary>
    /// Verifies that the agent notifies callers of all messages
    /// including function calling ones when using invoke streaming with a plugin.
    /// </summary>
    [RetryFact(3, 10_000)]
    public virtual async Task InvokeStreamingWithPluginNotifiesForAllMessagesAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;
        agent.Kernel.Plugins.AddFromType<MenuPlugin>();
        var notifiedMessages = new List<ChatMessageContent>();

        // Act
        var asyncResults = agent.InvokeStreamingAsync(
            new ChatMessageContent(AuthorRole.User, "What is the special soup?"),
            this.Fixture.AgentThread,
            options: new()
            {
                KernelArguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
                OnIntermediateMessage = (message) =>
                {
                    notifiedMessages.Add(message);
                    return Task.CompletedTask;
                }
            });

        // Assert
        var results = await asyncResults.ToListAsync();
        var resultString = string.Join(string.Empty, results.Select(x => x.Message.Content));
        Assert.Contains("Clam Chowder", resultString);

        Assert.Equal(3, notifiedMessages.Count);
        Assert.Contains(notifiedMessages[0].Items, x => x is FunctionCallContent);
        Assert.Contains(notifiedMessages[1].Items, x => x is FunctionResultContent);

        var functionCallContent = notifiedMessages[0].Items.OfType<FunctionCallContent>().First();
        var functionResultContent = notifiedMessages[1].Items.OfType<FunctionResultContent>().First();

        Assert.Equal("GetSpecials", functionCallContent.FunctionName);
        Assert.Equal("GetSpecials", functionResultContent.FunctionName);

        Assert.Contains("Clam Chowder", notifiedMessages[2].Content);
    }

    public Task InitializeAsync()
    {
        this._agentFixture = createAgentFixture();
        return this._agentFixture.InitializeAsync();
    }

    public Task DisposeAsync()
    {
        return this._agentFixture.DisposeAsync();
    }
}
