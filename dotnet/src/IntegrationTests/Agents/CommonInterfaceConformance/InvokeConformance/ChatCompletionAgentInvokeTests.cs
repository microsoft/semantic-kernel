// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents.CommonInterfaceConformance.InvokeConformance;

public class ChatCompletionAgentInvokeTests() : InvokeTests(() => new ChatCompletionAgentFixture())
{
    /// <summary>
    /// Verifies that the agent returns a function call content when using
    /// autoinvoke = false, and accepts a manual function call result to generate
    /// the final response.
    /// </summary>
    [RetryFact(3, 5000)]
    public virtual async Task InvokeWithPluginAndManualInvokeAsync()
    {
        // Arrange
        var agent = this.Fixture.Agent;
        agent.Kernel.Plugins.AddFromType<MenuPlugin>();
        var notifiedMessages = new List<ChatMessageContent>();

        var agentThread = new ChatHistoryAgentThread();

        // Act - Invoke 1
        var asyncResults = agent.InvokeAsync(
            new ChatMessageContent(AuthorRole.User, "What is the special soup?"),
            agentThread,
            options: new()
            {
                KernelArguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) }),
                OnIntermediateMessage = (message) =>
                {
                    notifiedMessages.Add(message);
                    return Task.CompletedTask;
                }
            });

        // Assert - Invoke 1 results
        var results = await asyncResults.ToArrayAsync();
        Assert.Single(results);

        Assert.Contains(results[0].Message.Items, x => x is FunctionCallContent);
        var functionCallContent = results[0].Message.Items.OfType<FunctionCallContent>().First();

        // Add the function call to the chat history so that it can be used in the next invocation.
        agentThread.ChatHistory.Add(results[0].Message);

        // Manually call function so that we can pass the result to the next invocation.
        var functionCallResult = await functionCallContent.InvokeAsync(agent.Kernel);
        var functionCallResultMessage = functionCallResult.ToChatMessage();

        // Act - Invoke 2
        asyncResults = agent.InvokeAsync(
            functionCallResultMessage,
            agentThread,
            options: new()
            {
                KernelArguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(autoInvoke: false) }),
                OnIntermediateMessage = (message) =>
                {
                    notifiedMessages.Add(message);
                    return Task.CompletedTask;
                }
            });

        // Assert - Invoke 2 results
        results = await asyncResults.ToArrayAsync();
        Assert.Single(results);

        Assert.Contains("Clam Chowder", results[0].Message.Content);
    }
}
