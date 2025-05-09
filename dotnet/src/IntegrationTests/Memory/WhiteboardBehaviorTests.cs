// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Memory;

/// <summary>
/// Contains tests for the <see cref="WhiteboardBehavior"/> class.
/// </summary>
public class WhiteboardBehaviorTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<WhiteboardBehaviorTests>()
            .Build();

    private readonly ITestOutputHelper _output;
    private readonly Kernel _kernel;

    public WhiteboardBehaviorTests(ITestOutputHelper output)
    {
        AzureOpenAIConfiguration configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>()!;

        var kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: configuration.ChatDeploymentName!,
            endpoint: configuration.Endpoint,
            credentials: new AzureCliCredential());
        this._kernel = kernelBuilder.Build();
        this._output = output;
    }

    [Theory]
    [MemberData(nameof(AddMessagesToWhiteboardData))]
    public async Task CanAddMessagesToWhiteboardAsync(ChatMessage[] chatMessages, string[][] expectedWhiteboardContent)
    {
        // Arrange
        var whiteboardBehavior = new WhiteboardBehavior(this._kernel);

        // Act
        foreach (var chatMessage in chatMessages)
        {
            await whiteboardBehavior.OnNewMessageAsync(null, chatMessage);
        }

        // Assert
        await whiteboardBehavior.WhenProcessingCompleteAsync();
        var whiteboardContent = await whiteboardBehavior.OnModelInvokeAsync(new List<ChatMessage> { new(ChatRole.User, string.Empty) });
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

    public static IEnumerable<object[]> AddMessagesToWhiteboardData()
    {
        yield return new object[]
        {
            new[]
            {
                new ChatMessage(ChatRole.User, "Hello") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.Assistant, "Hello, how can I help you?") { AuthorName = "Copilot" },
                new ChatMessage(ChatRole.User, "I want to create a presentation") { AuthorName = "Siobhan" },
            },
            new string[][] { new string[] { "REQUIREMENT", "presentation" } }
        };
        yield return new object[]
        {
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
            }
        };
        yield return new object[]
        {
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
            }
        };
        yield return new object[]
        {
            new[]
            {
                new ChatMessage(ChatRole.User, "I am looking to buy a lamp") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "I want it to be energy efficient") { AuthorName = "Siobhan" },
                new ChatMessage(ChatRole.User, "It should fit my red colour scheme.") { AuthorName = "Siobhan" },
            },
            new string[][]
            {
                new string[] { "REQUIREMENT", "lamp" }, new string[] { "REQUIREMENT", "red" }, new string[] { "REQUIREMENT", "efficient" }
            }
        };
    }
}
