// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class AggregatorAgentTests()
{
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIAssistantAgentTests>()
            .Build();

    /// <summary>
    /// Integration test for <see cref="AggregatorAgent"/> non-streamed nested response.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AggregatorAgentFlatResponseAsync()
    {
        // Arrange
        AggregatorAgent aggregatorAgent = new(() => this.CreateChatProvider())
        {
            Mode = AggregatorMode.Flat,
        };

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "1"));

        // Act
        ChatMessageContent[] responses = await chat.InvokeAsync(aggregatorAgent).ToArrayAsync();

        // Assert
        ChatMessageContent[] innerHistory = await chat.GetChatMessagesAsync(aggregatorAgent).ToArrayAsync();
        Assert.Equal(6, innerHistory.Length);
        Assert.Equal(5, responses.Length);
        Assert.NotNull(responses[4].Content);
        AssertResponseContent(responses[4]);
    }

    /// <summary>
    /// Integration test for <see cref="AggregatorAgent"/> non-streamed nested response.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AggregatorAgentNestedResponseAsync()
    {
        // Arrange
        AggregatorAgent aggregatorAgent = new(() => this.CreateChatProvider())
        {
            Mode = AggregatorMode.Nested,
        };

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "1"));

        // Act
        ChatMessageContent[] responses = await chat.InvokeAsync(aggregatorAgent).ToArrayAsync();

        // Assert
        ChatMessageContent[] innerHistory = await chat.GetChatMessagesAsync(aggregatorAgent).ToArrayAsync();
        Assert.Equal(6, innerHistory.Length);
        Assert.Single(responses);
        Assert.NotNull(responses[0].Content);
        AssertResponseContent(responses[0]);
    }

    /// <summary>
    /// Integration test for <see cref="AggregatorAgent"/> non-streamed response.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AggregatorAgentFlatStreamAsync()
    {
        // Arrange
        AggregatorAgent aggregatorAgent = new(() => this.CreateChatProvider())
        {
            Mode = AggregatorMode.Flat,
        };

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "1"));

        // Act
        StreamingChatMessageContent[] streamedResponse = await chat.InvokeStreamingAsync(aggregatorAgent).ToArrayAsync();

        // Assert
        ChatMessageContent[] fullResponses = await chat.GetChatMessagesAsync().ToArrayAsync();
        ChatMessageContent[] innerHistory = await chat.GetChatMessagesAsync(aggregatorAgent).ToArrayAsync();
        Assert.NotEmpty(streamedResponse);
        Assert.Equal(6, innerHistory.Length);
        Assert.Equal(6, fullResponses.Length);
        Assert.NotNull(fullResponses[0].Content);
        AssertResponseContent(fullResponses[0]);
    }

    /// <summary>
    /// Integration test for <see cref="AggregatorAgent"/> non-streamed response.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task AggregatorAgentNestedStreamAsync()
    {
        // Arrange
        AggregatorAgent aggregatorAgent = new(() => this.CreateChatProvider())
        {
            Mode = AggregatorMode.Nested,
        };

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, "1"));

        // Act
        StreamingChatMessageContent[] streamedResponse = await chat.InvokeStreamingAsync(aggregatorAgent).ToArrayAsync();

        // Assert
        ChatMessageContent[] fullResponses = await chat.GetChatMessagesAsync().ToArrayAsync();
        ChatMessageContent[] innerHistory = await chat.GetChatMessagesAsync(aggregatorAgent).ToArrayAsync();
        Assert.NotEmpty(streamedResponse);
        Assert.Equal(6, innerHistory.Length);
        Assert.Equal(2, fullResponses.Length);
        Assert.NotNull(fullResponses[0].Content);
        AssertResponseContent(fullResponses[0]);
    }

    private static void AssertResponseContent(ChatMessageContent response)
    {
        // Counting is hard
        Assert.True(
            response.Content!.Contains("five", StringComparison.OrdinalIgnoreCase) ||
            response.Content!.Contains("six", StringComparison.OrdinalIgnoreCase) ||
            response.Content!.Contains("seven", StringComparison.OrdinalIgnoreCase) ||
            response.Content!.Contains("eight", StringComparison.OrdinalIgnoreCase),
            $"Content: {response}");
    }

    private AgentGroupChat CreateChatProvider()
    {
        // Arrange
        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        this._kernelBuilder.AddAzureOpenAIChatCompletion(
            configuration.ChatDeploymentName!,
            configuration.Endpoint,
            new AzureCliCredential());

        Kernel kernel = this._kernelBuilder.Build();

        ChatCompletionAgent agent =
            new()
            {
                Kernel = kernel,
                Instructions = "Your job is to count.  Always add one to the previous number and respond using the english word for that number, without explanation.",
            };

        return new AgentGroupChat(agent)
        {
            ExecutionSettings = new()
            {
                TerminationStrategy = new CountTerminationStrategy(5)
            }
        };
    }

    private sealed class CountTerminationStrategy(int maximumResponseCount) : TerminationStrategy
    {
        // Terminate when the assistant has responded N times.
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken)
            => Task.FromResult(history.Count(message => message.Role == AuthorRole.Assistant) >= maximumResponseCount);
    }
}
