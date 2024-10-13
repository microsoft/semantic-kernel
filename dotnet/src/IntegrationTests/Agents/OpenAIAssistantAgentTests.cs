// Copyright (c) Microsoft. All rights reserved.
using System;
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using System.ClientModel;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using System.ClientModel;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
using System.ClientModel;
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
using System.ClientModel;
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            OpenAIClientProvider.ForOpenAI(openAISettings.ApiKey),
            openAISettings.ChatModelId!,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            OpenAIClientProvider.ForOpenAI(openAISettings.ApiKey),
            openAISettings.ChatModelId!,
=======
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
            openAISettings.ChatModelId!,
            openAISettings.ModelId,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
            openAISettings.ChatModelId!,
            openAISettings.ModelId,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
            openAISettings.ChatModelId!,
            openAISettings.ModelId,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
            input,
            expectedAnswerContains);
    }

    /// <summary>
    /// Integration test for <see cref="OpenAIAssistantAgent"/> using function calling
    /// and targeting Azure OpenAI services.
    /// </summary>
    [RetryTheory(typeof(HttpOperationException))]
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
    [Theory/*(Skip = "No supported endpoint configured.")*/]
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    [Theory/*(Skip = "No supported endpoint configured.")*/]
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
    [Theory/*(Skip = "No supported endpoint configured.")*/]
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    [Theory/*(Skip = "No supported endpoint configured.")*/]
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    [InlineData("What is the special soup?", "Clam Chowder")]
    public async Task AzureOpenAIAssistantAgentAsync(string input, string expectedAnswerContains)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        await this.ExecuteAgentAsync(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< main
            OpenAIClientProvider.ForAzureOpenAI(azureOpenAIConfiguration.ApiKey, new Uri(azureOpenAIConfiguration.Endpoint)),
=======
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            OpenAIClientProvider.ForAzureOpenAI(azureOpenAIConfiguration.ApiKey, new Uri(azureOpenAIConfiguration.Endpoint)),
=======
=======
            OpenAIClientProvider.ForAzureOpenAI(azureOpenAIConfiguration.ApiKey, new Uri(azureOpenAIConfiguration.Endpoint)),
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            OpenAIClientProvider.ForAzureOpenAI(azureOpenAIConfiguration.ApiKey, new Uri(azureOpenAIConfiguration.Endpoint)),
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            OpenAIClientProvider.ForOpenAI(openAISettings.ApiKey),
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            OpenAIClientProvider.ForOpenAI(openAISettings.ApiKey),
=======
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            OpenAIClientProvider.ForOpenAI(new ApiKeyCredential(openAISettings.ApiKey)),
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> upstream/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> upstream/main
=======
            OpenAIClientProvider.ForAzureOpenAI(azureOpenAIConfiguration.ApiKey, new Uri(azureOpenAIConfiguration.Endpoint)),
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            OpenAIClientProvider.ForAzureOpenAI(azureOpenAIConfiguration.ApiKey, new Uri(azureOpenAIConfiguration.Endpoint)),
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
            OpenAIClientProvider.ForAzureOpenAI(azureOpenAIConfiguration.ApiKey, new Uri(azureOpenAIConfiguration.Endpoint)),
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< main
=======
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                kernel,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                kernel,
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
                kernel,
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
                kernel,
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                config,
                new(modelName)
                {
                    Instructions = "Answer questions about the menu.",
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                });
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                });
=======
                },
                kernel);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                },
                kernel);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> upstream/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
>>>>>>> upstream/main
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> upstream/main
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> upstream/main
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

        KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
        kernel.Plugins.Add(plugin);

        OpenAIAssistantAgent agent =
            await OpenAIAssistantAgent.CreateAsync(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                kernel,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
                kernel,
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
                kernel,
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
                kernel,
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                config,
                new(modelName)
                {
                    Instructions = "Answer questions about the menu.",
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                },
                kernel);
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
                },
                kernel);
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
                });

        AgentGroupChat chat = new();
        chat.Add(new ChatMessageContent(AuthorRole.User, input));

        // Act
        StringBuilder builder = new();
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        await foreach (var message in chat.InvokeAsync(agent))
        try
=======
        await foreach (var message in chat.InvokeStreamingAsync(agent))
>>>>>>> upstream/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        await foreach (var message in chat.InvokeAsync(agent))
        try
        await foreach (var message in chat.InvokeStreamingAsync(agent))
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        await foreach (var message in chat.InvokeAsync(agent))
        try
        await foreach (var message in chat.InvokeStreamingAsync(agent))
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        await foreach (var message in chat.InvokeAsync(agent))
        try
        await foreach (var message in chat.InvokeStreamingAsync(agent))
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< main
=======
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

        // Assert
        ChatMessageContent[] history = await chat.GetChatMessagesAsync().ToArrayAsync();
        Assert.Contains(expected, builder.ToString(), StringComparison.OrdinalIgnoreCase);
        Assert.Contains(expected, history.First().Content, StringComparison.OrdinalIgnoreCase);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> upstream/main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
>>>>>>> upstream/main
=======
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> upstream/main
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> upstream/main
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
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
