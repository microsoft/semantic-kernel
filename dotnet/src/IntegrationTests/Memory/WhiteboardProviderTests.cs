// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Memory;

/// <summary>
/// Contains tests for the <see cref="WhiteboardProvider"/> class.
/// </summary>
public class WhiteboardProviderTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<WhiteboardProviderTests>()
            .Build();

    private readonly ITestOutputHelper _output;
    private readonly IChatClient _chatClient;

    public WhiteboardProviderTests(ITestOutputHelper output)
    {
        this._output = output;

        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;
        this._chatClient = new AzureOpenAIClient(new Uri(configuration.Endpoint), new AzureCliCredential())
            .GetChatClient(configuration.ChatDeploymentName)
            .AsIChatClient();
    }

    [Fact]
    public Task AddsRequirementToWhiteboardAsync()
    {
        return this.CanAddMessagesToWhiteboardAsync(
            new[]
            {
                new ChatMessage(ChatRole.User, "Hello") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "Hello, how can I help you?") { AuthorName = "Copilot" },
                new ChatMessage(ChatRole.User, "I want to create a presentation") { AuthorName = "Siobhan" },
            },
            new string[][] { new string[] { "REQUIREMENT", "presentation" } });
    }

    [Fact]
    public Task AddsRequirementsAndProposalToWhiteboardAsync()
    {
        return this.CanAddMessagesToWhiteboardAsync(
            new[]
            {
                new ChatMessage(ChatRole.User, "I want to create a presentation") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "What would you like it to be about?") { AuthorName = "Copilot" },
                new ChatMessage(ChatRole.User, "I want to feature our top 3 customers.") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "I want it to be professional looking.") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "I want a grey colour scheme.") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "Would you like me to create a presentation with Contoso, Northwind and Adventureworks? I'll make it professional with a grey colour scheme.") { AuthorName = "Copilot" },
            },
            new string[][]
            {
                new string[] { "REQUIREMENT", "presentation" },
                new string[] { "REQUIREMENT", "customers" },
                new string[] { "PROPOSAL", "Contoso", "Northwind" }
            });
    }

    [Fact]
    public Task AddsDecisionToWhiteboardAsync()
    {
        return this.CanAddMessagesToWhiteboardAsync(
            new[]
            {
                new ChatMessage(ChatRole.User, "I want to create a presentation") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "What would you like it to be about?") { AuthorName = "Copilot" },
                new ChatMessage(ChatRole.User, "I want to feature our top 3 customers.") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "I want it to be professional looking.") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "I want a grey colour scheme.") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "Would you like me to create a presentation with Contoso, Northwind and Adventureworks? I'll make it professional with a grey colour scheme.") { AuthorName = "Copilot" },
                new ChatMessage(ChatRole.User, "That sounds good, let's to that.") { AuthorName = "Siobhan" },
            },
            new string[][]
            {
                new string[] { "DECISION", "presentation", "Contoso", "professional" }
            });
    }

    [Fact]
    public Task AddsProposalToWhiteboardAsync()
    {
        return this.CanAddMessagesToWhiteboardAsync(
            new[]
            {
                new ChatMessage(ChatRole.User, "I am looking to create a VM") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "It should be in Europe") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "It should have 16GB or RAM") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "It should have 4 cores") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "OK, shall I create a VM for you in Europe with 16GB of RAM, 4 cores and with the name `VM-Europe`?") { AuthorName = "Copilot" },
            },
            new string[][]
            {
                new string[] { "PROPOSAL", "Europe", "16GB", "4", "VM", "VM-Europe" }
            });
    }

    [Fact]
    public Task AddsActionToWhiteboardAsync()
    {
        return this.CanAddMessagesToWhiteboardAsync(
            new[]
            {
                new ChatMessage(ChatRole.User, "I am looking to create a VM") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "I need you to give me the required location, amount of RAM you need, and number of cores required.") { AuthorName = "Copilot" },
                new ChatMessage(ChatRole.User, "It should be in Europe") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "It should have 16GB or RAM") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "It should have 4 cores") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "OK, shall I create a VM for you in Europe with 16GB of RAM, 4 cores and with the name `VM-Europe`?") { AuthorName = "Copilot" },
                new ChatMessage(ChatRole.User, "Yes, please go ahead and create that.") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "OK, I've created the VM for you.") { AuthorName = "Copilot" },
            },
            new string[][]
            {
                new string[] { "ACTION", "Europe", "16GB", "4", "VM" }
            });
    }

    private async Task CanAddMessagesToWhiteboardAsync(ChatMessage[] chatMessages, string[][] expectedWhiteboardContent)
    {
        // Arrange
        var WhiteboardProvider = new WhiteboardProvider(this._chatClient);

        // Act
        foreach (var chatMessage in chatMessages)
        {
            await WhiteboardProvider.MessageAddingAsync(null, chatMessage);
        }

        // Assert
        await WhiteboardProvider.WhenProcessingCompleteAsync();
        var aiContextAdditions = await WhiteboardProvider.ModelInvokingAsync(new List<ChatMessage> { new(ChatRole.User, string.Empty) });
        var whiteboardContent = aiContextAdditions.Instructions!;
        this._output.WriteLine(string.Join(Environment.NewLine, whiteboardContent));

        var whiteboardLines = whiteboardContent.Split('\n');
        foreach (var expectedContent in expectedWhiteboardContent)
        {
            bool foundAllInOneLine = false;
            foreach (var line in whiteboardLines)
            {
                bool foundAll = expectedContent.All(line.Contains);
                foundAllInOneLine = foundAllInOneLine || foundAll;
            }

            Assert.True(foundAllInOneLine, $"Expected content '{string.Join(", ", expectedContent)}' not found in whiteboard content.");
        }
    }
}
