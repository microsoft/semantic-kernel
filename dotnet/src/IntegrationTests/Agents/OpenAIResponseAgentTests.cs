// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;
using OpenAI.Responses;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Agents;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OpenAIResponseAgentTests(ITestOutputHelper output)
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIResponseAgentTests>()
            .Build();

    /// <summary>
    /// Integration test for <see cref="OpenAIResponseAgent"/>.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("Answer all queries in English and French.", "Paris")]
    public async Task OpenAIResponseAgentInvokeAsync(string input, string expectedAnswerContains)
    {
        var configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(configuration);

        await this.ExecuteAgentAsync(
            this.CreateClient(configuration),
            configuration.ChatModelId!,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIResponseAgent"/> using a thread.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("Answer all queries in English and French.", "Paris")]
    public async Task OpenAIResponseAgentInvokeWithThreadAsync(string input, string expectedAnswerContains)
    {
        var configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(configuration);

        // Arrange
        var client = this.CreateClient(configuration);
        Kernel kernel = new();
        OpenAIResponseAgent agent = new(client)
        {
            Instructions = "Answer all queries in English and French."
        };

        // Act & Assert
        AgentThread? thread = null;
        try
        {
            StringBuilder builder = new();
            await foreach (var responseItem in agent.InvokeAsync(input))
            {
                Assert.NotNull(responseItem);
                Assert.NotNull(responseItem.Message);
                Assert.NotNull(responseItem.Thread);
                Assert.Equal(AuthorRole.Assistant, responseItem.Message.Role);

                builder.Append(responseItem.Message.Content);
                thread = responseItem.Thread;
            }
        }
        finally
        {
            Assert.NotNull(thread);
            await thread.DeleteAsync();

            // Copy of the thread that doesn't have the deleted state
            thread = new OpenAIResponseAgentThread(client, thread.Id!);
            await Assert.ThrowsAsync<AgentThreadOperationException>(async () => await thread.DeleteAsync());
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIResponseAgent"/> using streaming.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("Answer all queries in English and French.", "Paris")]
    public async Task OpenAIResponseAgentInvokeStreamingAsync(string input, string expectedAnswerContains)
    {
        OpenAIConfiguration configuration = this.ReadConfiguration();
        Assert.NotNull(configuration);

        await this.ExecuteStreamingAgentAsync(
            this.CreateClient(configuration),
            configuration.ChatModelId!,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIResponseAgent"/> adding override instructions to a thread on invocation via custom options.
    /// </summary>
    [RetryFact(typeof(HttpOperationException))]
    public async Task OpenAIResponseAgentInvokeStreamingWithThreadAsync()
    {
        // Arrange
        OpenAIConfiguration configuration = this.ReadConfiguration();
        OpenAIResponseClient client = this.CreateClient(configuration);
        OpenAIResponseAgent agent = new(client)
        {
            Instructions = "Answer all queries in English and French."
        };

        OpenAIResponseAgentThread agentThread = new(client);

        // Act
        string? responseText = null;
        try
        {
            var message = new ChatMessageContent(AuthorRole.User, "What is the capital of France?");
            var responseMessages = await agent.InvokeStreamingAsync(
                message,
                agentThread,
                new OpenAIResponseAgentInvokeOptions()
                {
                    AdditionalInstructions = "Respond to all user questions with 'Computer says no'.",
                }).ToArrayAsync();

            responseText = string.Join(string.Empty, responseMessages.Select(ri => ri.Message.Content));
        }
        finally
        {
            await agentThread.DeleteAsync();
        }

        // Assert
        Assert.NotNull(responseText);
        Assert.Contains("Computer says no", responseText);
    }

    #region private
    /// <summary>
    /// Enable or disable logging for the tests.
    /// </summary>
    private bool EnableLogging { get; set; } = true;


    private async Task ExecuteAgentAsync(
        OpenAIResponseClient client,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();
        OpenAIResponseAgent agent = new(client)
        {
            Instructions = "Answer all queries in English and French."
        };

        // Act & Assert
        StringBuilder builder = new();
        await foreach (var responseItem in agent.InvokeAsync(input))
        {
            Assert.NotNull(responseItem);
            Assert.NotNull(responseItem.Message);
            Assert.NotNull(responseItem.Thread);
            Assert.Equal(AuthorRole.Assistant, responseItem.Message.Role);

            builder.Append(responseItem.Message.Content);
        }
    }

    private async Task ExecuteStreamingAgentAsync(
        OpenAIResponseClient client,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();
        OpenAIResponseAgent agent = new(client)
        {
            Instructions = "Answer all queries in English and French."
        };

        // Act
        StringBuilder builder = new();
        AgentThread? thread = null;
        await foreach (var responseItem in agent.InvokeStreamingAsync(input))
        {
            builder.Append(responseItem.Message.Content);
            thread = responseItem.Thread;
        }

        // Assert
        Assert.NotNull(thread);
        Assert.Contains(expected, builder.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    private static void AssertMessageValid(ChatMessageContent message)
    {
        if (message.Items.OfType<FunctionResultContent>().Any())
        {
            Assert.Equal(AuthorRole.Tool, message.Role);
            return;
        }

        if (message.Items.OfType<FunctionCallContent>().Any())
        {
            Assert.Equal(AuthorRole.Assistant, message.Role);
            return;
        }

        Assert.Equal(string.IsNullOrEmpty(message.AuthorName) ? AuthorRole.User : AuthorRole.Assistant, message.Role);
    }

    private OpenAIConfiguration ReadConfiguration()
    {
        OpenAIConfiguration? configuration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(configuration);
        return configuration;
    }

    private OpenAIResponseClient CreateClient(OpenAIConfiguration configuration)
    {
        OpenAIClientOptions options = new();

        if (this.EnableLogging)
        {
            options.ClientLoggingOptions = new ClientLoggingOptions
            {
                EnableLogging = true,
                EnableMessageLogging = true,
                EnableMessageContentLogging = true,
                LoggerFactory = new RedirectOutput(output),
            };
        }

        return new OpenAIResponseClient(configuration.ChatModelId, new ApiKeyCredential(configuration.ApiKey), options);
    }

    public sealed class MenuPlugin
    {
        [KernelFunction, Description("Provides a list of specials from the menu.")]
        [System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1024:Use properties where appropriate", Justification = "Too smart")]
        public string GetSpecials()
        {
            return @"
Special Soup: Clam Chowder
Special Salad: Cobb Salad
Special Drink: Chai Tea
";
        }

        [KernelFunction, Description("Provides the price of the requested menu item.")]
        public string GetItemPrice(
            [Description("The name of the menu item.")]
            string menuItem)
        {
            return "$9.99";
        }
    }
    #endregion
}
