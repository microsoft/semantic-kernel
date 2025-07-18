// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Identity;
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
    [InlineData("What is the capital of France?", "Paris", true, true)]
    [InlineData("What is the capital of France?", "Paris", true, false)]
    [InlineData("What is the capital of France?", "Paris", false, true)]
    [InlineData("What is the capital of France?", "Paris", false, false)]
    public async Task OpenAIResponseAgentInvokeAsync(string input, string expectedAnswerContains, bool isOpenAI, bool storeEnabled)
    {
        OpenAIResponseClient client = this.CreateClient(isOpenAI);

        await this.ExecuteAgentAsync(
            client,
            storeEnabled,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIResponseAgent"/> using a thread.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the capital of France?", "Paris", true, true)]
    [InlineData("What is the capital of France?", "Paris", true, false)]
    [InlineData("What is the capital of France?", "Paris", false, true)]
    [InlineData("What is the capital of France?", "Paris", false, false)]
    public async Task OpenAIResponseAgentInvokeWithThreadAsync(string input, string expectedAnswerContains, bool isOpenAI, bool storeEnabled)
    {
        // Arrange
        OpenAIResponseClient client = this.CreateClient(isOpenAI);
        OpenAIResponseAgent agent = new(client)
        {
            StoreEnabled = storeEnabled,
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

            // Assert
            Assert.NotNull(thread);
            Assert.Contains(expectedAnswerContains, builder.ToString(), StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            Assert.NotNull(thread);

            if (thread.Id is not null)
            {
                await thread.DeleteAsync();
            }
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIResponseAgent"/> using a function calling.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the special soup and how much does it cost?", "Clam Chowder", true, true)]
    [InlineData("What is the special soup and how much does it cost?", "Clam Chowder", true, false)]
    [InlineData("What is the special soup and how much does it cost?", "Clam Chowder", false, true)]
    [InlineData("What is the special soup and how much does it cost?", "Clam Chowder", false, false)]
    public async Task OpenAIResponseAgentInvokeWithFunctionCallingAsync(string input, string expectedAnswerContains, bool isOpenAI, bool storeEnabled)
    {
        // Arrange
        OpenAIResponseClient client = this.CreateClient(isOpenAI);
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        OpenAIResponseAgent agent = new(client)
        {
            StoreEnabled = storeEnabled,
            Instructions = "Answer questions about the menu."
        };
        agent.Kernel.Plugins.Add(plugin);

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

                builder.Append(responseItem.Message.Content);
                thread = responseItem.Thread;
            }

            // Assert
            Assert.NotNull(thread);
            Assert.Contains(expectedAnswerContains, builder.ToString(), StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            Assert.NotNull(thread);

            if (thread.Id is not null)
            {
                await thread.DeleteAsync();
            }
        }
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIResponseAgent"/> using streaming.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the capital of France?", "Paris", true, true)]
    [InlineData("What is the capital of France?", "Paris", true, false)]
    [InlineData("What is the capital of France?", "Paris", false, true)]
    [InlineData("What is the capital of France?", "Paris", false, false)]
    public async Task OpenAIResponseAgentInvokeStreamingAsync(string input, string expectedAnswerContains, bool isOpenAI, bool storeEnabled)
    {
        OpenAIResponseClient client = this.CreateClient(isOpenAI);

        await this.ExecuteStreamingAgentAsync(
            client,
            storeEnabled,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIResponseAgent"/> adding override instructions to a thread on invocation via custom options.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData(true, false)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task OpenAIResponseAgentInvokeStreamingWithThreadAsync(bool isOpenAI, bool storeEnabled)
    {
        // Arrange
        OpenAIResponseClient client = this.CreateClient(isOpenAI);
        OpenAIResponseAgent agent = new(client)
        {
            StoreEnabled = storeEnabled,
            Instructions = "Answer all queries in English and French."
        };

        AgentThread agentThread = storeEnabled ? new OpenAIResponseAgentThread(client) : new ChatHistoryAgentThread();

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
            if (agentThread.Id is not null)
            {
                await agentThread.DeleteAsync();
            }
        }

        // Assert
        Assert.NotNull(responseText);
        Assert.Contains("Computer says no", responseText);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIResponseAgent"/> adding override instructions to a thread on invocation via custom options.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the special soup and how much does it cost?", "Clam Chowder", true, true)]
    [InlineData("What is the special soup and how much does it cost?", "Clam Chowder", true, false)]
    [InlineData("What is the special soup and how much does it cost?", "Clam Chowder", false, true)]
    [InlineData("What is the special soup and how much does it cost?", "Clam Chowder", false, false)]
    public async Task OpenAIResponseAgentInvokeStreamingWithFunctionCallingAsync(string input, string expectedAnswerContains, bool isOpenAI, bool storeEnabled)
    {
        // Arrange
        OpenAIResponseClient client = this.CreateClient(isOpenAI);
        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        OpenAIResponseAgent agent = new(client)
        {
            StoreEnabled = storeEnabled,
            Instructions = "Answer questions about the menu."
        };
        agent.Kernel.Plugins.Add(plugin);

        // Act
        StringBuilder builder = new();
        AgentThread? agentThread = null;
        try
        {
            var message = new ChatMessageContent(AuthorRole.User, input);
            await foreach (var responseItem in agent.InvokeStreamingAsync(input))
            {
                builder.Append(responseItem.Message.Content);
                agentThread = responseItem.Thread;
            }
        }
        finally
        {
            Assert.NotNull(agentThread);

            if (agentThread.Id is not null)
            {
                await agentThread.DeleteAsync();
            }
        }

        // Assert
        var responseText = builder.ToString();
        Assert.NotNull(responseText);
        Assert.Contains(expectedAnswerContains, responseText);
    }

    #region private
    /// <summary>
    /// Enable or disable logging for the tests.
    /// </summary>
    private bool EnableLogging { get; set; } = true;

    private async Task ExecuteAgentAsync(
        OpenAIResponseClient client,
        bool storeEnabled,
        string input,
        string expected)
    {
        // Arrange
        OpenAIResponseAgent agent = new(client)
        {
            StoreEnabled = storeEnabled,
            Instructions = "Answer all queries in English and French."
        };

        // Act & Assert
        StringBuilder builder = new();
        AgentThread? thread = null;
        await foreach (var responseItem in agent.InvokeAsync(input))
        {
            Assert.NotNull(responseItem);
            Assert.NotNull(responseItem.Message);
            Assert.NotNull(responseItem.Thread);
            Assert.Equal(AuthorRole.Assistant, responseItem.Message.Role);

            builder.Append(responseItem.Message.Content);
            thread = responseItem.Thread;
        }

        // Assert
        Assert.NotNull(thread);
        Assert.Contains(expected, builder.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    private async Task ExecuteStreamingAgentAsync(
        OpenAIResponseClient client,
        bool storeEnabled,
        string input,
        string expected)
    {
        // Arrange
        OpenAIResponseAgent agent = new(client)
        {
            StoreEnabled = storeEnabled,
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

    private OpenAIResponseClient CreateClient(bool isOpenAI)
    {
        OpenAIResponseClient client;
        if (isOpenAI)
        {
            client = this.CreateClient(this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>());
        }
        else
        {
            client = this.CreateClient(this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>());
        }

        return client;
    }

    private OpenAIResponseClient CreateClient(OpenAIConfiguration? configuration)
    {
        Assert.NotNull(configuration);

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

    private OpenAIResponseClient CreateClient(AzureOpenAIConfiguration? configuration)
    {
        Assert.NotNull(configuration);

        AzureOpenAIClientOptions options = new();

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

        var azureClient = new AzureOpenAIClient(new Uri(configuration.Endpoint), new AzureCliCredential(), options);
        return azureClient.GetOpenAIResponseClient(configuration.ChatDeploymentName);
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
