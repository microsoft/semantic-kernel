// Copyright (c) Microsoft. All rights reserved.
using System;
using System.ClientModel;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;

namespace SemanticKernel.IntegrationTests.Agents;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OpenAIAssistantAgentTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIAssistantAgentTests>()
            .Build();

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Open AI services.
    /// </summary>
    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task OpenAIAssistantAgentTestAsync(string input, string expectedAnswerContains)
    {
        OpenAIConfiguration openAISettings = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        Assert.NotNull(openAISettings);

        await this.ExecuteAgentAsync(
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
            openAISettings.ChatModelId!,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task AzureOpenAIAssistantAgentAsync(string input, string expectedAnswerContains)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        await this.ExecuteAgentAsync(
            OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint)),
            azureOpenAIConfiguration.ChatDeploymentName!,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Open AI services.
    /// </summary>
    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task OpenAIAssistantAgentStreamingAsync(string input, string expectedAnswerContains)
    {
        OpenAIConfiguration openAISettings = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>()!;
        Assert.NotNull(openAISettings);

        await this.ExecuteStreamingAgentAsync(
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
            openAISettings.ModelId,
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task AzureOpenAIAssistantAgentStreamingAsync(string input, string expectedAnswerContains)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        await this.ExecuteStreamingAgentAsync(
            OpenAIClientProvider.ForAzureOpenAI(new AzureCliCredential(), new Uri(azureOpenAIConfiguration.Endpoint)),
            azureOpenAIConfiguration.ChatDeploymentName!,
            input,
            expectedAnswerContains);
    }

    private async Task ExecuteAgentAsync(
        OpenAIClientProvider config,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                config,
                new(modelName)
                {
                    Instructions = "Answer questions about the menu.",
                },
                kernel);

        try
        {
            AgentGroupChat chat = new();
            chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

            // Act
            StringBuilder builder = new();
            await foreach (var message in chat.InvokeAsync(agent))
            {
                builder.Append(message.Content);
            }

            // Assert
            Assert.Contains(expected, builder.ToString(), StringComparison.OrdinalIgnoreCase);
        }
        finally
        {
            await agent.DeleteAsync();
        }
    }

    private async Task ExecuteStreamingAgentAsync(
        OpenAIClientProvider config,
        string modelName,
        string input,
        string expected)
    {
        // Arrange
        Kernel kernel = new();

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
                config,
                new(modelName)
                {
                    Instructions = "Answer questions about the menu.",
                },
                kernel);

        AgentGroupChat chat = new();
        chat.AddChatMessage(new ChatMessageContent(AuthorRole.User, input));

        // Act
        StringBuilder builder = new();
        await foreach (var message in chat.InvokeStreamingAsync(agent))
        {
            builder.Append(message.Content);
        }

        // Assert
        ChatMessageContent[] history = await chat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Contains(expected, builder.ToString(), StringComparison.OrdinalIgnoreCase);
        Assert.Contains(expected, history.First().Content, StringComparison.OrdinalIgnoreCase);
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
}
